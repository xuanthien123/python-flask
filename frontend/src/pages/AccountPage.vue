<script setup>
import { computed, onMounted, reactive, ref } from 'vue'

import { changePassword, fetchCurrentUser, updateProfile } from '../api/auth.js'
import AppIcon from '../components/AppIcon.vue'
import { showSuccess } from '../stores/notices.js'
import { saveUser } from '../stores/session.js'

// Cùng luật độ dài với Flask (ChangePasswordSchema)
const MIN_PASSWORD_LENGTH = 8

// value là chữ lưu trong DB. Cột sex cho tối đa 10 ký tự.
const SEX_OPTIONS = [
  { value: '', label: 'Không chọn' },
  { value: 'male', label: 'Nam' },
  { value: 'female', label: 'Nữ' },
  { value: 'other', label: 'Khác' },
]

const ROLE_LABELS = {
  admin: 'Quản trị viên',
}

const profile = ref(null)
const isLoading = ref(true)
const loadErrorText = ref('')

const profileForm = reactive({
  name: '',
  address: '',
  date_of_birth: '',
  sex: '',
})
const isSavingProfile = ref(false)
const profileErrorText = ref('')
const profileFieldErrors = ref({})

const passwordForm = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: '',
})
const isSavingPassword = ref(false)
const passwordErrorText = ref('')
const passwordFieldErrors = ref({})

// Chữ cái đầu của tên, hiện trong vòng tròn thay cho ảnh đại diện
const avatarLetter = computed(() => {
  if (profile.value === null || profile.value.name === '') {
    return '?'
  }
  const firstLetter = profile.value.name.charAt(0)
  return firstLetter.toUpperCase()
})

const roleLabels = computed(() => {
  if (profile.value === null || profile.value.roles.length === 0) {
    return ['Người dùng']
  }
  return profile.value.roles.map((roleName) => {
    const roleLabel = ROLE_LABELS[roleName]
    if (roleLabel === undefined) {
      return roleName
    }
    return roleLabel
  })
})

const isEmailVerified = computed(() => {
  if (profile.value === null) {
    return false
  }
  return profile.value.email_verified_at !== null
})

const emailVerifiedText = computed(() => {
  if (!isEmailVerified.value) {
    return 'Email chưa xác minh'
  }
  const verifiedDate = new Date(profile.value.email_verified_at)
  return `Email đã xác minh ngày ${verifiedDate.toLocaleDateString('vi-VN')}`
})

// Flask trả ngày sinh dạng "1995-08-20", đổi thành "20/08/1995" cho dễ đọc.
// Tách chuỗi thay vì dùng new Date, vì new Date có thể lệch một ngày do múi giờ.
const dateOfBirthText = computed(() => {
  if (profile.value === null || profile.value.date_of_birth === null) {
    return ''
  }
  const dateParts = profile.value.date_of_birth.split('-')
  const year = dateParts[0]
  const month = dateParts[1]
  const day = dateParts[2]
  return `${day}/${month}/${year}`
})

// DB có thể đang lưu giá trị giới tính không nằm trong danh sách (ví dụ "Nam").
// Thêm giá trị đó vào ô chọn, để bấm Lưu không vô tình xoá mất nó.
const sexOptions = computed(() => {
  if (profile.value === null || !profile.value.sex) {
    return SEX_OPTIONS
  }

  const currentSex = profile.value.sex
  const isKnownValue = SEX_OPTIONS.some((option) => option.value === currentSex)
  if (isKnownValue) {
    return SEX_OPTIONS
  }

  const extraOption = { value: currentSex, label: currentSex }
  return SEX_OPTIONS.concat([extraOption])
})

// Flask trả null cho ô chưa điền, ô nhập trên trang cần chuỗi rỗng
function convertNullToEmpty(value) {
  if (value === null) {
    return ''
  }
  return value
}

// Ngược lại: ô để trống thì gửi null, Flask hiểu là xoá giá trị cũ
function convertEmptyToNull(text) {
  const trimmedText = text.trim()
  if (trimmedText === '') {
    return null
  }
  return trimmedText
}

function fillProfileForm(user) {
  profileForm.name = user.name
  profileForm.address = convertNullToEmpty(user.address)
  // Flask trả ngày dạng "1995-08-20", đúng dạng ô <input type="date"> cần
  profileForm.date_of_birth = convertNullToEmpty(user.date_of_birth)
  profileForm.sex = convertNullToEmpty(user.sex)
}

function showProfile(user) {
  profile.value = user
  fillProfileForm(user)
  // Cập nhật luôn tên trên thanh menu
  saveUser(user)
}

async function loadProfile() {
  try {
    const responseBody = await fetchCurrentUser()
    showProfile(responseBody.data)
  } catch (error) {
    loadErrorText.value = error.detailText
  } finally {
    isLoading.value = false
  }
}

async function saveProfile() {
  isSavingProfile.value = true
  profileErrorText.value = ''
  profileFieldErrors.value = {}

  const payload = {
    name: profileForm.name,
    address: convertEmptyToNull(profileForm.address),
    date_of_birth: convertEmptyToNull(profileForm.date_of_birth),
    sex: convertEmptyToNull(profileForm.sex),
  }

  try {
    const responseBody = await updateProfile(payload)
    showProfile(responseBody.data)
    showSuccess('Đã lưu thông tin cá nhân')
  } catch (error) {
    profileErrorText.value = error.message
    profileFieldErrors.value = error.fieldErrors || {}
  } finally {
    isSavingProfile.value = false
  }
}

// Kiểm ngay trên trình duyệt để báo lỗi tức thì. Trả về true khi hợp lệ.
function checkPasswordFields() {
  if (passwordForm.newPassword.length < MIN_PASSWORD_LENGTH) {
    passwordFieldErrors.value = { new_password: `Cần ít nhất ${MIN_PASSWORD_LENGTH} ký tự` }
    return false
  }
  if (passwordForm.newPassword !== passwordForm.confirmPassword) {
    passwordFieldErrors.value = { confirm_password: 'Hai mật khẩu chưa giống nhau' }
    return false
  }
  return true
}

function clearPasswordForm() {
  passwordForm.currentPassword = ''
  passwordForm.newPassword = ''
  passwordForm.confirmPassword = ''
}

async function savePassword() {
  passwordErrorText.value = ''
  passwordFieldErrors.value = {}

  const isValid = checkPasswordFields()
  if (!isValid) {
    return
  }

  isSavingPassword.value = true
  try {
    await changePassword(passwordForm.currentPassword, passwordForm.newPassword)
    clearPasswordForm()
    showSuccess('Đã đổi mật khẩu')
  } catch (error) {
    passwordErrorText.value = error.message
    passwordFieldErrors.value = error.fieldErrors || {}
  } finally {
    isSavingPassword.value = false
  }
}

onMounted(() => {
  loadProfile()
})
</script>

<template>
  <section class="page">
    <header class="page-header">
      <div>
        <h1 class="page-title">Tài khoản</h1>
        <p class="page-subtitle">Thông tin cá nhân và mật khẩu của bạn</p>
      </div>
    </header>

    <div v-if="isLoading" class="card loading-state">
      <span class="spinner"></span>
      Đang tải thông tin…
    </div>

    <div v-else-if="loadErrorText" class="alert alert-error">
      <AppIcon name="alert-circle" />
      <span>{{ loadErrorText }}</span>
    </div>

    <div v-else class="account-grid">
      <aside class="card profile-card">
        <span class="avatar avatar-large">{{ avatarLetter }}</span>
        <div>
          <p class="profile-name">{{ profile.name }}</p>
          <p class="profile-email">{{ profile.email }}</p>
        </div>
        <div class="chip-list chip-list-center">
          <span v-for="roleLabel in roleLabels" :key="roleLabel" class="badge">
            <AppIcon name="shield" :size="12" />
            {{ roleLabel }}
          </span>
        </div>

        <ul class="profile-meta">
          <li :class="{ 'text-success': isEmailVerified }">
            <AppIcon :name="isEmailVerified ? 'check-circle' : 'mail'" :size="16" />
            {{ emailVerifiedText }}
          </li>
          <li v-if="dateOfBirthText">
            <AppIcon name="calendar" :size="16" />
            Sinh ngày {{ dateOfBirthText }}
          </li>
          <li v-if="profile.address">
            <AppIcon name="map-pin" :size="16" />
            {{ profile.address }}
          </li>
        </ul>
      </aside>

      <div class="card-stack">
        <form class="card" @submit.prevent="saveProfile">
          <header class="card-header">
            <h2 class="card-title">Thông tin cá nhân</h2>
            <p class="card-subtitle">Tên, địa chỉ, ngày sinh và giới tính</p>
          </header>

          <div class="card-body form">
            <div v-if="profileErrorText" class="alert alert-error">
              <AppIcon name="alert-circle" />
              <span>{{ profileErrorText }}</span>
            </div>

            <div class="form-row">
              <label class="form-field" :class="{ 'has-error': profileFieldErrors.name }">
                <span class="form-label">Họ tên <span class="required-mark">*</span></span>
                <input
                  v-model.trim="profileForm.name"
                  class="input"
                  type="text"
                  maxlength="255"
                  required
                />
                <span v-if="profileFieldErrors.name" class="field-error">
                  {{ profileFieldErrors.name }}
                </span>
              </label>

              <label class="form-field">
                <span class="form-label">Email</span>
                <!-- Flask chưa có API đổi email nên chỉ cho xem -->
                <input :value="profile.email" class="input" type="email" disabled />
                <span class="form-hint">Dùng để đăng nhập, chưa đổi được.</span>
              </label>
            </div>

            <label class="form-field" :class="{ 'has-error': profileFieldErrors.address }">
              <span class="form-label">Địa chỉ</span>
              <input
                v-model="profileForm.address"
                class="input"
                type="text"
                maxlength="512"
                placeholder="Không bắt buộc"
              />
              <span v-if="profileFieldErrors.address" class="field-error">
                {{ profileFieldErrors.address }}
              </span>
            </label>

            <div class="form-row">
              <label
                class="form-field"
                :class="{ 'has-error': profileFieldErrors.date_of_birth }"
              >
                <span class="form-label">Ngày sinh</span>
                <input v-model="profileForm.date_of_birth" class="input" type="date" />
                <span v-if="profileFieldErrors.date_of_birth" class="field-error">
                  {{ profileFieldErrors.date_of_birth }}
                </span>
              </label>

              <label class="form-field" :class="{ 'has-error': profileFieldErrors.sex }">
                <span class="form-label">Giới tính</span>
                <select v-model="profileForm.sex" class="input">
                  <option v-for="option in sexOptions" :key="option.value" :value="option.value">
                    {{ option.label }}
                  </option>
                </select>
                <span v-if="profileFieldErrors.sex" class="field-error">
                  {{ profileFieldErrors.sex }}
                </span>
              </label>
            </div>
          </div>

          <footer class="card-footer">
            <button type="submit" class="button button-primary" :disabled="isSavingProfile">
              {{ isSavingProfile ? 'Đang lưu…' : 'Lưu thay đổi' }}
            </button>
          </footer>
        </form>

        <form class="card" @submit.prevent="savePassword">
          <header class="card-header">
            <h2 class="card-title">Đổi mật khẩu</h2>
            <p class="card-subtitle">Mật khẩu mới cần ít nhất {{ MIN_PASSWORD_LENGTH }} ký tự</p>
          </header>

          <div class="card-body form">
            <div v-if="passwordErrorText" class="alert alert-error">
              <AppIcon name="alert-circle" />
              <span>{{ passwordErrorText }}</span>
            </div>

            <label
              class="form-field"
              :class="{ 'has-error': passwordFieldErrors.current_password }"
            >
              <span class="form-label">Mật khẩu hiện tại</span>
              <input
                v-model="passwordForm.currentPassword"
                class="input"
                type="password"
                autocomplete="current-password"
                required
              />
              <span v-if="passwordFieldErrors.current_password" class="field-error">
                {{ passwordFieldErrors.current_password }}
              </span>
            </label>

            <div class="form-row">
              <label
                class="form-field"
                :class="{ 'has-error': passwordFieldErrors.new_password }"
              >
                <span class="form-label">Mật khẩu mới</span>
                <input
                  v-model="passwordForm.newPassword"
                  class="input"
                  type="password"
                  autocomplete="new-password"
                  :minlength="MIN_PASSWORD_LENGTH"
                  required
                />
                <span v-if="passwordFieldErrors.new_password" class="field-error">
                  {{ passwordFieldErrors.new_password }}
                </span>
              </label>

              <label
                class="form-field"
                :class="{ 'has-error': passwordFieldErrors.confirm_password }"
              >
                <span class="form-label">Nhập lại mật khẩu mới</span>
                <input
                  v-model="passwordForm.confirmPassword"
                  class="input"
                  type="password"
                  autocomplete="new-password"
                  required
                />
                <span v-if="passwordFieldErrors.confirm_password" class="field-error">
                  {{ passwordFieldErrors.confirm_password }}
                </span>
              </label>
            </div>
          </div>

          <footer class="card-footer">
            <button type="submit" class="button button-primary" :disabled="isSavingPassword">
              {{ isSavingPassword ? 'Đang lưu…' : 'Đổi mật khẩu' }}
            </button>
          </footer>
        </form>
      </div>
    </div>
  </section>
</template>
