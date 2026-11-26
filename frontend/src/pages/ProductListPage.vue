<script setup>
import { onMounted, reactive, ref } from 'vue'

import { fetchProductPage, fetchProductSummary } from '../api/products.js'

// Số dòng mỗi trang. Flask mặc định 20, cho tối đa 100
const PRODUCTS_PER_PAGE = 10

// value phải khớp PRODUCT_SORT_KEYS bên Flask, có '-' phía trước là giảm dần
const SORT_OPTIONS = [
  { value: 'id', label: 'Cũ nhất trước' },
  { value: '-id', label: 'Mới nhất trước' },
  { value: 'name', label: 'Tên A → Z' },
  { value: '-name', label: 'Tên Z → A' },
  { value: 'price', label: 'Giá thấp → cao' },
  { value: '-price', label: 'Giá cao → thấp' },
]

// ref(): biến mà đổi giá trị thì giao diện tự vẽ lại.
// Trong <script> đọc, ghi qua .value; trong <template> thì viết thẳng tên biến.
const products = ref([])
const pageInfo = ref({ page: 1, per_page: PRODUCTS_PER_PAGE, total: 0, pages: 0 })
const summary = ref(null)
const isLoading = ref(false)
const errorText = ref('')

// reactive(): giống ref nhưng dành cho object, đọc thẳng filters.q, không cần .value.
// Các ô trong form gắn vào đây bằng v-model: gõ vào ô là giá trị ở đây đổi theo.
const filters = reactive({
  q: '',
  min_price: '',
  max_price: '',
  sort: 'id',
})

// Định dạng số kiểu Việt Nam: 1234567.5 thành "1.234.567,5"
const numberFormatter = new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 2 })

function formatNumber(value) {
  return numberFormatter.format(value)
}

function joinCategoryNames(categories) {
  if (categories.length === 0) {
    return '—'
  }
  const categoryNames = categories.map((category) => category.name)
  return categoryNames.join(', ')
}

async function loadProducts(pageNumber) {
  isLoading.value = true
  errorText.value = ''

  const queryParams = {
    q: filters.q,
    min_price: filters.min_price,
    max_price: filters.max_price,
    sort: filters.sort,
    page: pageNumber,
    per_page: PRODUCTS_PER_PAGE,
  }

  try {
    const responseBody = await fetchProductPage(queryParams)
    products.value = responseBody.data
    pageInfo.value = responseBody.meta
  } catch (error) {
    errorText.value = error.message
  } finally {
    // finally chạy cả khi thành công lẫn khi lỗi, để nút không kẹt ở trạng thái đang tải
    isLoading.value = false
  }
}

async function loadSummary() {
  try {
    const responseBody = await fetchProductSummary()
    summary.value = responseBody.data
  } catch (error) {
    errorText.value = error.message
  }
}

function applyFilters() {
  // Đổi bộ lọc thì số trang đang xem không còn đúng nữa, quay về trang 1
  loadProducts(1)
}

function resetFilters() {
  filters.q = ''
  filters.min_price = ''
  filters.max_price = ''
  filters.sort = 'id'
  loadProducts(1)
}

function goToPreviousPage() {
  loadProducts(pageInfo.value.page - 1)
}

function goToNextPage() {
  loadProducts(pageInfo.value.page + 1)
}

// onMounted: chạy một lần khi trang vừa hiện lên, lúc này mới gọi API lấy dữ liệu
onMounted(() => {
  loadSummary()
  loadProducts(1)
})
</script>

<template>
  <section class="page">
    <header class="page-header">
      <h1>Sản phẩm</h1>
      <p class="page-subtitle">Trang mẫu: đọc dữ liệu từ GET /api/products</p>
    </header>

    <!-- v-if: chỉ vẽ khối này khi đã có summary, tránh lỗi đọc summary.total_products khi còn null -->
    <div v-if="summary" class="summary-grid">
      <div class="summary-card">
        <span class="summary-label">Số sản phẩm</span>
        <strong class="summary-value">{{ formatNumber(summary.total_products) }}</strong>
      </div>
      <div class="summary-card">
        <span class="summary-label">Tổng số lượng tồn</span>
        <strong class="summary-value">{{ formatNumber(summary.total_quantity) }}</strong>
      </div>
      <div class="summary-card">
        <span class="summary-label">Giá trị tồn kho</span>
        <strong class="summary-value">{{ formatNumber(summary.total_inventory_value) }}</strong>
      </div>
    </div>

    <!-- .prevent: chặn trình duyệt tải lại cả trang khi bấm Lọc hoặc Enter -->
    <form class="filter-bar" @submit.prevent="applyFilters">
      <label class="field field-wide">
        <span>Tên sản phẩm</span>
        <input v-model.trim="filters.q" type="search" placeholder="Gõ tên để tìm" />
      </label>

      <label class="field">
        <span>Giá từ</span>
        <input v-model="filters.min_price" type="number" min="0" step="any" />
      </label>

      <label class="field">
        <span>Giá đến</span>
        <input v-model="filters.max_price" type="number" min="0" step="any" />
      </label>

      <label class="field">
        <span>Sắp xếp</span>
        <select v-model="filters.sort" @change="applyFilters">
          <option v-for="option in SORT_OPTIONS" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </select>
      </label>

      <div class="filter-actions">
        <button type="submit" class="button button-primary" :disabled="isLoading">Lọc</button>
        <button type="button" class="button" :disabled="isLoading" @click="resetFilters">
          Xoá lọc
        </button>
      </div>
    </form>

    <p v-if="errorText" class="alert-error">{{ errorText }}</p>

    <div class="table-wrap">
      <table class="product-table">
        <thead>
          <tr>
            <th class="column-id">ID</th>
            <th>Tên</th>
            <th class="column-number">Giá</th>
            <th class="column-number">Số lượng</th>
            <th>Danh mục</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="isLoading">
            <td colspan="5" class="table-message">Đang tải…</td>
          </tr>
          <tr v-else-if="products.length === 0">
            <td colspan="5" class="table-message">Không có sản phẩm nào khớp bộ lọc.</td>
          </tr>
          <!-- <template> không vẽ ra thẻ nào, chỉ dùng để gói v-else và v-for -->
          <template v-else>
            <!-- :key giúp Vue biết dòng nào là dòng nào khi danh sách đổi -->
            <tr v-for="product in products" :key="product.id">
              <td class="column-id">{{ product.id }}</td>
              <td>
                <div class="product-name">{{ product.name }}</div>
                <div v-if="product.description" class="product-description">
                  {{ product.description }}
                </div>
              </td>
              <td class="column-number">{{ formatNumber(product.price) }}</td>
              <td class="column-number">{{ formatNumber(product.quantity) }}</td>
              <td>{{ joinCategoryNames(product.categories) }}</td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>

    <footer class="pagination">
      <span class="pagination-info">
        Tổng {{ formatNumber(pageInfo.total) }} sản phẩm · Trang {{ pageInfo.page }} /
        {{ pageInfo.pages || 1 }}
      </span>
      <div class="pagination-buttons">
        <button
          type="button"
          class="button"
          :disabled="isLoading || pageInfo.page <= 1"
          @click="goToPreviousPage"
        >
          ← Trước
        </button>
        <button
          type="button"
          class="button"
          :disabled="isLoading || pageInfo.page >= pageInfo.pages"
          @click="goToNextPage"
        >
          Sau →
        </button>
      </div>
    </footer>
  </section>
</template>
