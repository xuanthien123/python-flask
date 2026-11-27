<script setup>
import { ref } from 'vue'
import { RouterLink } from 'vue-router'

import { requestPasswordReset } from '../api/auth.js'
import AppIcon from '../components/AppIcon.vue'
import AuthLayout from '../components/AuthLayout.vue'

const email = ref('')
const isSubmitting = ref(false)
const isSent = ref(false)
const errorText = ref('')
const fieldErrors = ref({})

async function submitRequest() {
  isSubmitting.value = true
  errorText.value = ''
  fieldErrors.value = {}

  try {
    await requestPasswordReset(email.value)
    isSent.value = true
  } catch (error) {
    errorText.value = error.message
    fieldErrors.value = error.fieldErrors || {}
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <AuthLayout
    icon="mail"
    title="Quên mật khẩu?"
    subtitle="Nhập email tài khoản, hệ thống sẽ gửi link để bạn đặt mật khẩu mới"
  >
    <!-- Flask trả cùng một câu dù email có tài khoản hay không,
         nên ở đây cũng chỉ nói "nếu", không khẳng định đã gửi -->
    <div v-if="isSent" class="alert alert-success">
      <AppIcon name="check-circle" />
      <div class="alert-content">
        <p>
          Nếu <strong>{{ email }}</strong> có tài khoản, link đặt lại mật khẩu đã được gửi tới
          email đó. Hãy mở hộp thư và bấm vào link.
        </p>
        <p>Link chỉ dùng được một lần và sẽ hết hạn sau một thời gian.</p>
      </div>
    </div>

    <form v-else class="form" @submit.prevent="submitRequest">
      <div v-if="errorText" class="alert alert-error">
        <AppIcon name="alert-circle" />
        <span>{{ errorText }}</span>
      </div>

      <div class="form-field" :class="{ 'has-error': fieldErrors.email }">
        <label class="form-label" for="forgot-email">Email</label>
        <div class="input-icon-wrap">
          <AppIcon name="mail" :size="16" />
          <input
            id="forgot-email"
            v-model.trim="email"
            class="input input-large"
            type="email"
            autocomplete="email"
            placeholder="ban@example.com"
            required
          />
        </div>
        <span v-if="fieldErrors.email" class="field-error">{{ fieldErrors.email }}</span>
      </div>

      <button
        type="submit"
        class="button button-primary button-block button-large"
        :disabled="isSubmitting"
      >
        <span v-if="isSubmitting" class="spinner spinner-light"></span>
        {{ isSubmitting ? 'Đang gửi…' : 'Gửi link đặt lại mật khẩu' }}
      </button>
    </form>

    <RouterLink to="/login" class="auth-back-link">
      <AppIcon name="arrow-left" :size="16" />
      Quay lại đăng nhập
    </RouterLink>
  </AuthLayout>
</template>
