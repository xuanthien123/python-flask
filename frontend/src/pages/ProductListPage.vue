<script setup>
import { onMounted, reactive, ref } from 'vue'

import { fetchAllCategories } from '../api/categories.js'
import {
  deleteProduct,
  downloadProductExport,
  fetchProductPage,
  fetchProductSummary,
} from '../api/products.js'
import AppIcon from '../components/AppIcon.vue'
import PaginationBar from '../components/PaginationBar.vue'
import ProductFormDialog from '../components/ProductFormDialog.vue'
import ProductImportDialog from '../components/ProductImportDialog.vue'
import { showError, showSuccess } from '../stores/notices.js'
import { isAdmin } from '../stores/session.js'

// Số dòng mỗi trang. Flask mặc định 20, cho tối đa 100
const PRODUCTS_PER_PAGE = 10

// Số màu nền cho ô chữ cái đầu tên sản phẩm (class tone-0 tới tone-5 trong style.css)
const TONE_COUNT = 6

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
const categories = ref([])
const isLoading = ref(true)
const isExporting = ref(false)
const errorText = ref('')
// true khi đang lọc, để chọn câu cho trường hợp danh sách trống
const isFiltering = ref(false)

// Hộp thoại thêm, sửa: editingProductId là null khi thêm mới
const isFormOpen = ref(false)
const editingProductId = ref(null)
const isImportOpen = ref(false)

// reactive(): giống ref nhưng dành cho object, đọc thẳng filters.q, không cần .value.
// Các ô trong thanh lọc gắn vào đây bằng v-model: gõ vào ô là giá trị ở đây đổi theo.
const filters = reactive({
  q: '',
  category_id: '',
  min_price: '',
  max_price: '',
  sort: 'id',
})

// Bộ lọc đang áp dụng cho danh sách trên màn hình. Chỉ đổi khi bấm Lọc hoặc Xoá lọc,
// nên gõ dở trong ô lọc rồi bấm sang trang hay Xuất Excel vẫn đúng danh sách đang thấy.
let appliedFilterParams = {}

// Định dạng số kiểu Việt Nam: 1234567.5 thành "1.234.567,5"
const numberFormatter = new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 2 })

function formatNumber(value) {
  return numberFormatter.format(value)
}

// Ô tổng hợp: chưa tải xong thì hiện gạch ngang thay vì số 0 dễ gây hiểu nhầm
function formatSummaryValue(fieldName) {
  if (summary.value === null) {
    return '—'
  }
  return formatNumber(summary.value[fieldName])
}

function readFirstLetter(text) {
  const firstLetter = text.charAt(0)
  return firstLetter.toUpperCase()
}

// Cùng một sản phẩm luôn ra cùng một màu, vì màu chọn theo id
function pickToneClass(productId) {
  const toneIndex = productId % TONE_COUNT
  return `tone-${toneIndex}`
}

function buildFilterParams() {
  return {
    q: filters.q,
    category_id: filters.category_id,
    min_price: filters.min_price,
    max_price: filters.max_price,
    sort: filters.sort,
  }
}

function checkIsFiltering(filterParams) {
  if (filterParams.q !== '') {
    return true
  }
  if (filterParams.category_id !== '') {
    return true
  }
  if (filterParams.min_price !== '') {
    return true
  }
  if (filterParams.max_price !== '') {
    return true
  }
  return false
}

async function loadProducts(pageNumber) {
  isLoading.value = true
  errorText.value = ''

  // ...appliedFilterParams: chép hết bộ lọc đang áp dụng vào object mới, rồi thêm số trang
  const queryParams = {
    ...appliedFilterParams,
    page: pageNumber,
    per_page: PRODUCTS_PER_PAGE,
  }

  try {
    const responseBody = await fetchProductPage(queryParams)
    products.value = responseBody.data
    pageInfo.value = responseBody.meta
  } catch (error) {
    products.value = []
    errorText.value = error.detailText
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
    showError(error.detailText)
  }
}

async function loadCategories() {
  try {
    categories.value = await fetchAllCategories()
  } catch (error) {
    showError(error.detailText)
  }
}

function reloadCurrentPage() {
  loadProducts(pageInfo.value.page)
  loadSummary()
}

function applyFilters() {
  appliedFilterParams = buildFilterParams()
  isFiltering.value = checkIsFiltering(appliedFilterParams)
  // Đổi bộ lọc thì số trang đang xem không còn đúng nữa, quay về trang 1
  loadProducts(1)
}

function resetFilters() {
  filters.q = ''
  filters.category_id = ''
  filters.min_price = ''
  filters.max_price = ''
  filters.sort = 'id'
  applyFilters()
}

function openCreateForm() {
  editingProductId.value = null
  isFormOpen.value = true
}

function openEditForm(product) {
  editingProductId.value = product.id
  isFormOpen.value = true
}

function closeForm() {
  isFormOpen.value = false
}

function handleProductSaved(savedProduct) {
  if (editingProductId.value === null) {
    showSuccess(`Đã thêm sản phẩm "${savedProduct.name}"`)
  } else {
    showSuccess(`Đã lưu sản phẩm "${savedProduct.name}"`)
  }
  isFormOpen.value = false
  reloadCurrentPage()
}

async function confirmAndDeleteProduct(product) {
  // confirm: hộp hỏi có sẵn của trình duyệt, bấm OK trả true, bấm Huỷ trả false
  const isConfirmed = window.confirm(
    `Xoá sản phẩm "${product.name}"?\nViệc này không hoàn tác được.`,
  )
  if (!isConfirmed) {
    return
  }

  try {
    await deleteProduct(product.id)
    showSuccess(`Đã xoá sản phẩm "${product.name}"`)

    // Xoá dòng cuối cùng của một trang thì trang đó trống, lùi về trang trước
    let pageNumber = pageInfo.value.page
    if (products.value.length === 1 && pageNumber > 1) {
      pageNumber = pageNumber - 1
    }
    loadProducts(pageNumber)
    loadSummary()
  } catch (error) {
    showError(error.detailText)
  }
}

function handleImported(createdCount) {
  isImportOpen.value = false
  showSuccess(`Đã nhập ${createdCount} sản phẩm`)
  reloadCurrentPage()
}

async function exportProducts() {
  isExporting.value = true
  try {
    await downloadProductExport(appliedFilterParams)
    showSuccess('Đã tải file Excel')
  } catch (error) {
    showError(error.detailText)
  } finally {
    isExporting.value = false
  }
}

// onMounted: chạy một lần khi trang vừa hiện lên, lúc này mới gọi API lấy dữ liệu
onMounted(() => {
  applyFilters()
  loadSummary()
  loadCategories()
})
</script>

<template>
  <section class="page">
    <header class="page-header">
      <div>
        <h1 class="page-title">Sản phẩm</h1>
        <p class="page-subtitle">Xem, tìm và quản lý hàng trong kho</p>
      </div>

      <!-- Nút quản lý chỉ hiện cho admin. Flask cũng chặn người không phải admin. -->
      <div v-if="isAdmin()" class="page-actions">
        <button type="button" class="button" :disabled="isExporting" @click="exportProducts">
          <AppIcon name="download" :size="16" />
          {{ isExporting ? 'Đang xuất…' : 'Xuất Excel' }}
        </button>
        <button type="button" class="button" @click="isImportOpen = true">
          <AppIcon name="upload" :size="16" />
          Nhập Excel
        </button>
        <button type="button" class="button button-primary" @click="openCreateForm">
          <AppIcon name="plus" :size="16" />
          Thêm sản phẩm
        </button>
      </div>
      <span v-else class="view-only-pill">
        <AppIcon name="eye" :size="14" />
        Chỉ xem · cần quyền admin để sửa
      </span>
    </header>

    <div class="stat-grid">
      <div class="stat-card">
        <span class="stat-icon tone-0">
          <AppIcon name="package" :size="22" />
        </span>
        <div>
          <p class="stat-label">Số sản phẩm</p>
          <p class="stat-value">{{ formatSummaryValue('total_products') }}</p>
        </div>
      </div>
      <div class="stat-card">
        <span class="stat-icon tone-1">
          <AppIcon name="layers" :size="22" />
        </span>
        <div>
          <p class="stat-label">Tổng số lượng tồn</p>
          <p class="stat-value">{{ formatSummaryValue('total_quantity') }}</p>
        </div>
      </div>
      <div class="stat-card">
        <span class="stat-icon tone-2">
          <AppIcon name="coins" :size="22" />
        </span>
        <div>
          <p class="stat-label">Giá trị tồn kho (giá × số lượng)</p>
          <p class="stat-value">{{ formatSummaryValue('total_inventory_value') }}</p>
        </div>
      </div>
    </div>

    <div class="card data-card">
      <!-- .prevent: chặn trình duyệt tải lại cả trang khi bấm Lọc hoặc Enter -->
      <form class="data-toolbar" @submit.prevent="applyFilters">
        <div class="input-icon-wrap toolbar-search">
          <AppIcon name="search" :size="16" />
          <input
            v-model.trim="filters.q"
            class="input"
            type="search"
            placeholder="Tìm theo tên sản phẩm…"
            aria-label="Tìm theo tên sản phẩm"
          />
        </div>

        <select
          v-model="filters.category_id"
          class="input toolbar-select"
          aria-label="Lọc theo danh mục"
          @change="applyFilters"
        >
          <option value="">Tất cả danh mục</option>
          <option v-for="category in categories" :key="category.id" :value="category.id">
            {{ category.name }}
          </option>
        </select>

        <input
          v-model="filters.min_price"
          class="input toolbar-number"
          type="number"
          min="0"
          step="any"
          placeholder="Giá từ"
          aria-label="Giá từ"
        />
        <input
          v-model="filters.max_price"
          class="input toolbar-number"
          type="number"
          min="0"
          step="any"
          placeholder="Giá đến"
          aria-label="Giá đến"
        />

        <select
          v-model="filters.sort"
          class="input toolbar-select"
          aria-label="Sắp xếp"
          @change="applyFilters"
        >
          <option v-for="option in SORT_OPTIONS" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </select>

        <div class="toolbar-actions">
          <button type="submit" class="button button-primary" :disabled="isLoading">Lọc</button>
          <button
            type="button"
            class="button button-ghost"
            :disabled="isLoading"
            @click="resetFilters"
          >
            <AppIcon name="rotate" :size="16" />
            Xoá lọc
          </button>
        </div>
      </form>

      <div v-if="errorText" class="alert alert-error data-card-alert">
        <AppIcon name="alert-circle" />
        <span>{{ errorText }}</span>
      </div>

      <div v-if="isLoading" class="loading-state">
        <span class="spinner"></span>
        Đang tải sản phẩm…
      </div>

      <div v-else-if="products.length === 0" class="empty-state">
        <span class="empty-icon">
          <AppIcon name="inbox" :size="24" />
        </span>
        <p v-if="isFiltering" class="empty-title">Không tìm thấy sản phẩm phù hợp</p>
        <p v-else class="empty-title">Chưa có sản phẩm nào</p>
        <p v-if="isFiltering" class="empty-text">Thử đổi hoặc xoá bộ lọc.</p>
        <p v-else class="empty-text">Sản phẩm được thêm sẽ hiện ở đây.</p>
      </div>

      <div v-else class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>Sản phẩm</th>
              <th>Danh mục</th>
              <th class="column-number">Giá</th>
              <th class="column-number">Tồn kho</th>
              <th v-if="isAdmin()" class="column-actions">
                <span class="visually-hidden">Thao tác</span>
              </th>
            </tr>
          </thead>
          <tbody>
            <!-- :key giúp Vue biết dòng nào là dòng nào khi danh sách đổi -->
            <tr v-for="product in products" :key="product.id">
              <td>
                <div class="entity">
                  <span class="entity-thumb" :class="pickToneClass(product.id)">
                    {{ readFirstLetter(product.name) }}
                  </span>
                  <div class="entity-text">
                    <div class="entity-name">{{ product.name }}</div>
                    <div class="entity-meta">
                      #{{ product.id }}
                      <template v-if="product.description"> · {{ product.description }}</template>
                    </div>
                  </div>
                </div>
              </td>
              <td>
                <span v-if="product.categories.length === 0" class="text-muted">—</span>
                <div v-else class="chip-list">
                  <span v-for="category in product.categories" :key="category.id" class="chip">
                    {{ category.name }}
                  </span>
                </div>
              </td>
              <td class="column-number cell-strong">{{ formatNumber(product.price) }}</td>
              <td class="column-number">
                <span v-if="product.quantity === 0" class="badge badge-danger">Hết hàng</span>
                <span v-else>{{ formatNumber(product.quantity) }}</span>
              </td>
              <td v-if="isAdmin()" class="column-actions">
                <div class="row-actions">
                  <button
                    type="button"
                    class="icon-button"
                    title="Sửa"
                    :aria-label="`Sửa ${product.name}`"
                    @click="openEditForm(product)"
                  >
                    <AppIcon name="pencil" :size="16" />
                  </button>
                  <button
                    type="button"
                    class="icon-button icon-button-danger"
                    title="Xoá"
                    :aria-label="`Xoá ${product.name}`"
                    @click="confirmAndDeleteProduct(product)"
                  >
                    <AppIcon name="trash" :size="16" />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="data-footer">
        <PaginationBar
          :page-info="pageInfo"
          :is-loading="isLoading"
          item-label="sản phẩm"
          @change-page="loadProducts"
        />
      </div>
    </div>

    <ProductFormDialog
      v-if="isFormOpen"
      :product-id="editingProductId"
      :categories="categories"
      @close="closeForm"
      @saved="handleProductSaved"
    />

    <ProductImportDialog
      v-if="isImportOpen"
      @close="isImportOpen = false"
      @imported="handleImported"
    />
  </section>
</template>
