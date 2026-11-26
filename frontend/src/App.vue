<script setup>
import { RouterLink, RouterView } from 'vue-router'
</script>

<template>
  <div class="app-shell">
    <header class="topbar">
      <span class="brand">Product Manager</span>
      <nav class="topnav">
        <!-- RouterLink: đổi trang mà không tải lại cả trình duyệt -->
        <RouterLink to="/products">Sản phẩm</RouterLink>
      </nav>
    </header>

    <main class="app-main">
      <!-- RouterView: chỗ Vue Router đặt trang ứng với URL hiện tại -->
      <RouterView />
    </main>
  </div>
</template>
