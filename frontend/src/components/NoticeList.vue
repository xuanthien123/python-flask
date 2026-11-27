<script setup>
import { notices, removeNotice } from '../stores/notices.js'
import AppIcon from './AppIcon.vue'

function pickNoticeIcon(kind) {
  if (kind === 'success') {
    return 'check-circle'
  }
  return 'alert-circle'
}
</script>

<template>
  <!-- aria-live: trình đọc màn hình tự đọc thông báo mới hiện ra -->
  <div class="notice-list" aria-live="polite">
    <div
      v-for="notice in notices"
      :key="notice.id"
      class="notice"
      :class="`notice-${notice.kind}`"
      role="status"
    >
      <span class="notice-icon">
        <AppIcon :name="pickNoticeIcon(notice.kind)" :size="20" />
      </span>
      <span class="notice-text">{{ notice.text }}</span>
      <button
        type="button"
        class="icon-button icon-button-small"
        aria-label="Tắt thông báo"
        @click="removeNotice(notice.id)"
      >
        <AppIcon name="x" :size="16" />
      </button>
    </div>
  </div>
</template>
