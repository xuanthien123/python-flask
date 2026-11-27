<script setup>
// Khung hộp thoại nổi giữa màn hình, dùng chung cho form thêm, sửa và nhập file.
// Trang cha quyết định lúc nào hiện (bằng v-if) và nội dung bên trong (đặt giữa thẻ mở, thẻ đóng).
import { onBeforeUnmount, onMounted, ref } from 'vue'

import AppIcon from './AppIcon.vue'

defineProps({
  title: { type: String, required: true },
  // Dòng chữ nhỏ dưới tiêu đề, để trống thì không hiện
  subtitle: { type: String, default: '' },
})

// Báo lên trang cha khi người dùng muốn đóng (bấm ✕ hoặc phím Esc)
const emit = defineEmits(['close'])

// ref gắn vào thẻ <div class="modal"> để tìm ô nhập bên trong
const dialogElement = ref(null)

function closeOnEscape(event) {
  if (event.key === 'Escape') {
    emit('close')
  }
}

onMounted(() => {
  document.addEventListener('keydown', closeOnEscape)

  // Đưa con trỏ vào ô nhập đầu tiên để gõ được ngay, không phải bấm chuột
  const firstField = dialogElement.value.querySelector('input, select, textarea')
  if (firstField) {
    firstField.focus()
  }
})

// Hộp thoại đóng thì gỡ việc nghe phím, không thì phím Esc vẫn bị bắt mãi
onBeforeUnmount(() => {
  document.removeEventListener('keydown', closeOnEscape)
})
</script>

<template>
  <!-- Không đóng khi bấm ra ngoài, để lỡ tay bấm trượt không mất chữ đang gõ trong form -->
  <div class="modal-backdrop">
    <div ref="dialogElement" class="modal" role="dialog" aria-modal="true" :aria-label="title">
      <header class="modal-header">
        <div>
          <h2>{{ title }}</h2>
          <p v-if="subtitle" class="modal-subtitle">{{ subtitle }}</p>
        </div>
        <button type="button" class="icon-button" aria-label="Đóng" @click="emit('close')">
          <AppIcon name="x" />
        </button>
      </header>
      <div class="modal-body">
        <!-- slot: chỗ đặt nội dung trang cha truyền vào -->
        <slot />
      </div>
    </div>
  </div>
</template>
