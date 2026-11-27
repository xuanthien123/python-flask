<script setup>
import { reactive, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'

import { login } from '../api/auth.js'
import AppIcon from '../components/AppIcon.vue'
import AuthLayout from '../components/AuthLayout.vue'
import { showSuccess } from '../stores/notices.js'
import { saveLogin } from '../stores/session.js'

// useRoute: đọc URL hiện tại (route.query là phần ?a=1&b=2)
// useRouter: dùng để chuyển sang trang khác bằng code
const route = useRoute()
const router = useRouter()

const form = reactive({
  email: '',
  password: '',
})
const isPasswordVisible = ref(false)
const isSubmitting = ref(false)
const errorText = ref('')
const fieldErrors = ref({})

// ?expired=1 được gắn vào URL khi phiên đăng nhập cũ hết hạn
const isSessionExpired = route.query.expired === '1'

// Trang muốn vào trước khi bị bắt đăng nhập, ví dụ ?redirect=/account
function readRedirectPath() {
  const redirectPath = route.query.redirect

  // Chỉ nhận đường dẫn trong app (bắt đầu bằng đúng một dấu /).
  // "//trang-khac.com" là link sang trang web khác nên không nhận.
  const isInsideApp =
    typeof redirectPath === 'string' &&
    redirectPath.startsWith('/') &&
    !redirectPath.startsWith('//')

  if (isInsideApp) {
    return redirectPath
  }
  return '/products'
}

function togglePasswordVisible() {
  isPasswordVisible.value = !isPasswordVisible.value
}

async function submitLogin() {
  isSubmitting.value = true
  errorText.value = ''
  fieldErrors.value = {}

  try {
    const responseBody = await login(form.email, form.password)
    saveLogin(responseBody.data)
    showSuccess(`Xin chào ${responseBody.data.user.name}`)

    // replace: thay trang đăng nhập trong lịch sử, bấm Back không quay lại form này nữa
    const redirectPath = readRedirectPath()
    router.replace(redirectPath)
  } catch (error) {
    errorText.value = error.message
    fieldErrors.value = error.fieldErrors || {}
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <AuthLayout title="Chào mừng trở lại" subtitle="Đăng nhập để quản lý sản phẩm của bạn">
    <div v-if="isSessionExpired" class="alert alert-info">
      <AppIcon name="info" />
      <span>Phiên đăng nhập đã hết hạn, hãy đăng nhập lại.</span>
    </div>
    <div v-if="errorText" class="alert alert-error">
      <AppIcon name="alert-circle" />
      <span>{{ errorText }}</span>
    </div>

    <form class="form" @submit.prevent="submitLogin">
      <div class="form-field" :class="{ 'has-error': fieldErrors.email }">
        <label class="form-label" for="login-email">Email</label>
        <div class="input-icon-wrap">
          <AppIcon name="mail" :size="16" />
          <!-- autocomplete: để trình duyệt gợi ý email, mật khẩu đã lưu -->
          <input
            id="login-email"
            v-model.trim="form.email"
            class="input input-large"
            type="email"
            autocomplete="username"
            placeholder="ban@example.com"
            required
          />
        </div>
        <span v-if="fieldErrors.email" class="field-error">{{ fieldErrors.email }}</span>
      </div>

      <div class="form-field" :class="{ 'has-error': fieldErrors.password }">
        <div class="form-label-row">
          <label class="form-label" for="login-password">Mật khẩu</label>
          <RouterLink to="/forgot-password" class="link-small">Quên mật khẩu?</RouterLink>
        </div>
        <div class="input-icon-wrap">
          <AppIcon name="lock" :size="16" />
          <input
            id="login-password"
            v-model="form.password"
            class="input input-large input-with-action"
            :type="isPasswordVisible ? 'text' : 'password'"
            autocomplete="current-password"
            placeholder="Nhập mật khẩu"
            required
          />
          <button
            type="button"
            class="input-action"
            :aria-label="isPasswordVisible ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'"
            :title="isPasswordVisible ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'"
            @click="togglePasswordVisible"
          >
            <AppIcon :name="isPasswordVisible ? 'eye-off' : 'eye'" :size="16" />
          </button>
        </div>
        <span v-if="fieldErrors.password" class="field-error">{{ fieldErrors.password }}</span>
      </div>

      <button
        type="submit"
        class="button button-primary button-block button-large"
        :disabled="isSubmitting"
      >
        <span v-if="isSubmitting" class="spinner spinner-light"></span>
        {{ isSubmitting ? 'Đang đăng nhập…' : 'Đăng nhập' }}
      </button>
    </form>
  </AuthLayout>
</template>
