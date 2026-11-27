<script setup>
// Thanh phân trang dùng chung: đang xem dòng nào tới dòng nào, và hai nút Trước, Sau.
// Bấm nút thì báo lên trang cha số trang muốn xem, trang cha tự gọi API.
import { computed } from 'vue'

import AppIcon from './AppIcon.vue'

const props = defineProps({
  // meta Flask trả về: { page, per_page, total, pages }
  pageInfo: { type: Object, required: true },
  isLoading: { type: Boolean, default: false },
  // Chữ đứng sau tổng số, ví dụ "trong 25 sản phẩm"
  itemLabel: { type: String, default: 'dòng' },
})

const emit = defineEmits(['change-page'])

// Chưa có dòng nào thì Flask trả pages = 0, vẫn hiện "Trang 1 / 1" cho dễ đọc
const lastPage = computed(() => {
  if (props.pageInfo.pages === 0) {
    return 1
  }
  return props.pageInfo.pages
})

// Số thứ tự dòng đầu của trang đang xem. Trang 2, mỗi trang 10 dòng thì bắt đầu từ dòng 11
const firstRow = computed(() => {
  return (props.pageInfo.page - 1) * props.pageInfo.per_page + 1
})

// Số thứ tự dòng cuối. Trang cuối có thể ít dòng hơn nên không vượt quá tổng
const lastRow = computed(() => {
  const fullPageLastRow = props.pageInfo.page * props.pageInfo.per_page
  if (fullPageLastRow > props.pageInfo.total) {
    return props.pageInfo.total
  }
  return fullPageLastRow
})

const totalText = computed(() => props.pageInfo.total.toLocaleString('vi-VN'))
</script>

<template>
  <footer class="pagination">
    <span class="pagination-info">
      <template v-if="pageInfo.total === 0">Không có {{ itemLabel }} nào</template>
      <template v-else>
        Hiển thị <strong>{{ firstRow }}–{{ lastRow }}</strong> trong
        <strong>{{ totalText }}</strong> {{ itemLabel }}
      </template>
    </span>
    <div class="pagination-buttons">
      <button
        type="button"
        class="button button-small"
        :disabled="isLoading || pageInfo.page <= 1"
        @click="emit('change-page', pageInfo.page - 1)"
      >
        <AppIcon name="chevron-left" :size="16" />
        Trước
      </button>
      <span class="pagination-page">Trang {{ pageInfo.page }} / {{ lastPage }}</span>
      <button
        type="button"
        class="button button-small"
        :disabled="isLoading || pageInfo.page >= lastPage"
        @click="emit('change-page', pageInfo.page + 1)"
      >
        Sau
        <AppIcon name="chevron-right" :size="16" />
      </button>
    </div>
  </footer>
</template>
