<script setup>
// Khung chung của trang đăng nhập, quên mật khẩu, đặt lại mật khẩu:
// nền màu phủ kín màn hình, một thẻ trắng ở giữa. Nội dung riêng của từng trang đặt vào slot.
import AppIcon from './AppIcon.vue'

defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
  // Icon nhỏ phía trên tiêu đề, để trống thì không hiện
  icon: { type: String, default: '' },
})
</script>

<template>
  <div class="auth-screen">
    <div class="auth-card">
      <div class="auth-brand">
        <span class="brand-mark">
          <AppIcon name="package" :size="18" />
        </span>
        <span>Product Manager</span>
      </div>

      <header class="auth-header">
        <span v-if="icon" class="auth-icon">
          <AppIcon :name="icon" :size="22" />
        </span>
        <h1>{{ title }}</h1>
        <p v-if="subtitle" class="auth-subtitle">{{ subtitle }}</p>
      </header>

      <!-- slot: chỗ đặt nội dung riêng của từng trang -->
      <slot />
    </div>

    <p class="auth-footer">Quản lý sản phẩm, danh mục và tồn kho</p>
  </div>
</template>
