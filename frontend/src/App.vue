<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'

import { fetchCurrentUser, logout } from './api/auth.js'
import { checkApiHealth } from './api/health.js'
import AppIcon from './components/AppIcon.vue'
import NoticeList from './components/NoticeList.vue'
import { showSuccess } from './stores/notices.js'
import { clearSession, isAdmin, isLoggedIn, saveUser, session } from './stores/session.js'

// Cứ một phút hỏi lại /health một lần để chấm trạng thái luôn đúng
const HEALTH_CHECK_INTERVAL_MS = 60000

const route = useRoute()
const router = useRouter()

// null: chưa kiểm xong. Kiểm xong là { isHealthy, detailText }
const apiHealth = ref(null)
const isLoggingOut = ref(false)
let healthTimerId = null

// Có vẽ thanh menu hay không.
// Trang public (đăng nhập, quên, đặt lại mật khẩu) tự vẽ cả màn hình nên không có menu.
// Trang còn lại chỉ vào được khi đã đăng nhập (router đã chặn), nên có menu.
const showAppShell = computed(() => {
  // Lúc app vừa mở, router chưa chọn xong trang (matched rỗng): chưa vẽ gì cả,
  // tránh thanh menu chớp lên trước khi bị chuyển sang trang đăng nhập
  if (route.matched.length === 0) {
    return false
  }
  if (route.meta.public) {
    return false
  }
  return true
})

const userName = computed(() => {
  if (session.user === null) {
    return ''
  }
  return session.user.name
})

// Chữ cái đầu của tên, hiện trong vòng tròn thay cho ảnh đại diện
const avatarLetter = computed(() => {
  if (userName.value === '') {
    return '?'
  }
  const firstLetter = userName.value.charAt(0)
  return firstLetter.toUpperCase()
})

const roleText = computed(() => {
  if (isAdmin()) {
    return 'Quản trị viên'
  }
  return 'Người dùng'
})

const healthClass = computed(() => {
  if (apiHealth.value === null) {
    return 'health-unknown'
  }
  if (apiHealth.value.isHealthy) {
    return 'health-ok'
  }
  return 'health-error'
})

const healthText = computed(() => {
  if (apiHealth.value === null) {
    return 'Đang kiểm tra API…'
  }
  return apiHealth.value.detailText
})

async function refreshApiHealth() {
  apiHealth.value = await checkApiHealth()
}

// Quyền (roles) hay tên có thể đã đổi từ lần đăng nhập trước, hỏi lại máy chủ cho chắc
async function syncCurrentUser() {
  if (!isLoggedIn()) {
    return
  }

  try {
    const responseBody = await fetchCurrentUser()
    saveUser(responseBody.data)
  } catch {
    // Phiên hết hạn thì client.js đã tự đưa về trang đăng nhập.
    // Lỗi khác (máy chủ tạm lỗi) thì giữ thông tin cũ, không cần báo.
  }
}

async function logoutCurrentUser() {
  isLoggingOut.value = true

  try {
    await logout(session.refreshToken)
  } catch {
    // Máy chủ lỗi thì vẫn xoá phiên trên máy này, người dùng vẫn được đăng xuất
  } finally {
    clearSession()
    isLoggingOut.value = false
    showSuccess('Đã đăng xuất')
    router.push('/login')
  }
}

onMounted(() => {
  syncCurrentUser()
  refreshApiHealth()
  // setInterval: cứ mỗi HEALTH_CHECK_INTERVAL_MS lại chạy refreshApiHealth một lần
  healthTimerId = setInterval(refreshApiHealth, HEALTH_CHECK_INTERVAL_MS)
})

onBeforeUnmount(() => {
  clearInterval(healthTimerId)
})
</script>

<template>
  <div v-if="showAppShell" class="app-shell">
    <header class="topbar">
      <div class="topbar-inner">
        <RouterLink to="/products" class="brand">
          <span class="brand-mark">
            <AppIcon name="package" :size="18" />
          </span>
          <span class="brand-name">Product Manager</span>
        </RouterLink>

        <nav class="topnav" aria-label="Menu chính">
          <!-- RouterLink: đổi trang mà không tải lại cả trình duyệt -->
          <RouterLink to="/products">
            <AppIcon name="package" :size="16" />
            Sản phẩm
          </RouterLink>
          <RouterLink to="/categories">
            <AppIcon name="tag" :size="16" />
            Danh mục
          </RouterLink>
        </nav>

        <div class="topbar-right">
          <!-- title: chữ hiện ra khi rê chuột vào -->
          <span class="health-pill" :class="healthClass" :title="healthText">
            <span class="health-dot"></span>
            API
          </span>

          <RouterLink to="/account" class="user-chip" title="Tài khoản của bạn">
            <span class="avatar">{{ avatarLetter }}</span>
            <span class="user-text">
              <span class="user-name">{{ userName }}</span>
              <span class="user-role">{{ roleText }}</span>
            </span>
          </RouterLink>

          <button
            type="button"
            class="icon-button"
            title="Đăng xuất"
            aria-label="Đăng xuất"
            :disabled="isLoggingOut"
            @click="logoutCurrentUser"
          >
            <AppIcon name="logout" />
          </button>
        </div>
      </div>
    </header>

    <main class="app-main">
      <!-- RouterView: chỗ Vue Router đặt trang ứng với URL hiện tại -->
      <RouterView />
    </main>
  </div>

  <!-- Trang public: không có thanh menu, trang tự vẽ cả màn hình -->
  <RouterView v-else />

  <NoticeList />
</template>
