<script setup>
// Trang mở ra khi người dùng bấm link trong mail đặt lại mật khẩu.
// Link có dạng /reset-password?token=..., token là mã Flask tạo ra cho lần đặt lại này.
import { reactive, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

import { resetPassword } from '../api/auth.js'
import AppIcon from '../components/AppIcon.vue'
import AuthLayout from '../components/AuthLayout.vue'

// Cùng luật độ dài với Flask (ResetPasswordSchema)
const MIN_PASSWORD_LENGTH = 8

const route = useRoute()
const resetToken = route.query.token
const hasToken = typeof resetToken === 'string' && resetToken !== ''

const form = reactive({
  newPassword: '',
  confirmPassword: '',
})
const isSubmitting = ref(false)
const isDone = ref(false)
const errorText = ref('')
const fieldErrors = ref({})

// Kiểm ngay trên trình duyệt để báo lỗi tức thì, khỏi chờ gọi máy chủ.
// Trả về true khi hợp lệ.
function checkPasswordFields() {
  if (form.newPassword.length < MIN_PASSWORD_LENGTH) {
    fieldErrors.value = { new_password: `Cần ít nhất ${MIN_PASSWORD_LENGTH} ký tự` }
    return false
  }
  if (form.newPassword !== form.confirmPassword) {
    fieldErrors.value = { confirm_password: 'Hai mật khẩu chưa giống nhau' }
    return false
  }
  return true
}

async function submitNewPassword() {
  errorText.value = ''
  fieldErrors.value = {}

  const isValid = checkPasswordFields()
  if (!isValid) {
    return
  }

  isSubmitting.value = true
  try {
    await resetPassword(resetToken, form.newPassword)
    isDone.value = true
  } catch (error) {
    errorText.value = error.message
    fieldErrors.value = error.fieldErrors || {}
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <AuthLayout icon="key" title="Đặt mật khẩu mới" subtitle="Chọn mật khẩu mới cho tài khoản của bạn">
    <div v-if="!hasToken" class="alert alert-error">
      <AppIcon name="alert-circle" />
      <span>Link không đúng: thiếu mã đặt lại mật khẩu. Hãy mở lại link trong mail.</span>
    </div>

    <div v-else-if="isDone" class="alert alert-success">
      <AppIcon name="check-circle" />
      <span>Đã đổi mật khẩu. Giờ bạn đăng nhập bằng mật khẩu mới được rồi.</span>
    </div>

    <form v-else class="form" @submit.prevent="submitNewPassword">
      <div v-if="errorText" class="alert alert-error">
        <AppIcon name="alert-circle" />
        <div class="alert-content">
          <p>{{ errorText }}</p>
          <!-- Mã sai hay hết hạn thì nhập lại mật khẩu cũng vô ích, chỉ đường xin link mới -->
          <p v-if="fieldErrors.token">
            <RouterLink to="/forgot-password">Xin link mới</RouterLink>
          </p>
        </div>
      </div>

      <div class="form-field" :class="{ 'has-error': fieldErrors.new_password }">
        <label class="form-label" for="reset-new-password">Mật khẩu mới</label>
        <div class="input-icon-wrap">
          <AppIcon name="lock" :size="16" />
          <input
            id="reset-new-password"
            v-model="form.newPassword"
            class="input input-large"
            type="password"
            autocomplete="new-password"
            :minlength="MIN_PASSWORD_LENGTH"
            required
          />
        </div>
        <span v-if="fieldErrors.new_password" class="field-error">
          {{ fieldErrors.new_password }}
        </span>
        <span v-else class="form-hint">Ít nhất {{ MIN_PASSWORD_LENGTH }} ký tự</span>
      </div>

      <div class="form-field" :class="{ 'has-error': fieldErrors.confirm_password }">
        <label class="form-label" for="reset-confirm-password">Nhập lại mật khẩu mới</label>
        <div class="input-icon-wrap">
          <AppIcon name="lock" :size="16" />
          <input
            id="reset-confirm-password"
            v-model="form.confirmPassword"
            class="input input-large"
            type="password"
            autocomplete="new-password"
            required
          />
        </div>
        <span v-if="fieldErrors.confirm_password" class="field-error">
          {{ fieldErrors.confirm_password }}
        </span>
      </div>

      <button
        type="submit"
        class="button button-primary button-block button-large"
        :disabled="isSubmitting"
      >
        <span v-if="isSubmitting" class="spinner spinner-light"></span>
        {{ isSubmitting ? 'Đang lưu…' : 'Lưu mật khẩu mới' }}
      </button>
    </form>

    <RouterLink v-if="!hasToken" to="/forgot-password" class="auth-back-link">
      Xin link mới
    </RouterLink>
    <RouterLink v-else to="/login" class="auth-back-link">
      <AppIcon name="arrow-left" :size="16" />
      Đi tới đăng nhập
    </RouterLink>
  </AuthLayout>
</template>
