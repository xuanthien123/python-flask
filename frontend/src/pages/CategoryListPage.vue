<script setup>
import { computed, onMounted, reactive, ref } from 'vue'

import {
  createCategory,
  deleteCategory,
  fetchCategory,
  fetchCategoryPage,
  updateCategory,
} from '../api/categories.js'
import AppIcon from '../components/AppIcon.vue'
import ModalDialog from '../components/ModalDialog.vue'
import PaginationBar from '../components/PaginationBar.vue'
import { showError, showSuccess } from '../stores/notices.js'
import { isAdmin } from '../stores/session.js'

const CATEGORIES_PER_PAGE = 10

// Số màu nền cho ô icon (class tone-0 tới tone-5 trong style.css)
const TONE_COUNT = 6

const categories = ref([])
const pageInfo = ref({ page: 1, per_page: CATEGORIES_PER_PAGE, total: 0, pages: 0 })
const isLoading = ref(true)
const errorText = ref('')

// Chữ đang gõ trong ô tìm, và chữ của lần tìm gần nhất (dùng khi bấm sang trang)
const searchText = ref('')
const appliedSearchText = ref('')

// Hộp thoại thêm, sửa: editingCategoryId là null khi thêm mới
const isFormOpen = ref(false)
const editingCategoryId = ref(null)
const isFormLoading = ref(false)
const isSaving = ref(false)
const formErrorText = ref('')
const fieldErrors = ref({})
const form = reactive({
  name: '',
  description: '',
})

const formTitle = computed(() => {
  if (editingCategoryId.value === null) {
    return 'Thêm danh mục'
  }
  return 'Sửa danh mục'
})

// Cùng một danh mục luôn ra cùng một màu, vì màu chọn theo id
function pickToneClass(categoryId) {
  const toneIndex = categoryId % TONE_COUNT
  return `tone-${toneIndex}`
}

async function loadCategories(pageNumber) {
  isLoading.value = true
  errorText.value = ''

  try {
    const responseBody = await fetchCategoryPage({
      q: appliedSearchText.value,
      page: pageNumber,
      per_page: CATEGORIES_PER_PAGE,
    })
    categories.value = responseBody.data
    pageInfo.value = responseBody.meta
  } catch (error) {
    categories.value = []
    errorText.value = error.detailText
  } finally {
    isLoading.value = false
  }
}

function applySearch() {
  appliedSearchText.value = searchText.value
  loadCategories(1)
}

function resetSearch() {
  searchText.value = ''
  applySearch()
}

function resetForm() {
  form.name = ''
  form.description = ''
  formErrorText.value = ''
  fieldErrors.value = {}
}

function openCreateForm() {
  resetForm()
  editingCategoryId.value = null
  isFormOpen.value = true
}

async function openEditForm(category) {
  resetForm()
  editingCategoryId.value = category.id
  // Bật đang tải trước khi mở hộp thoại, để hộp thoại không hiện form trống
  isFormLoading.value = true
  isFormOpen.value = true

  try {
    // Lấy bản mới nhất từ máy chủ, phòng khi ai đó vừa sửa danh mục này
    const responseBody = await fetchCategory(category.id)
    form.name = responseBody.data.name

    // Không có mô tả thì Flask trả null, ô nhập cần chuỗi rỗng
    if (responseBody.data.description === null) {
      form.description = ''
    } else {
      form.description = responseBody.data.description
    }
  } catch (error) {
    formErrorText.value = error.message
  } finally {
    isFormLoading.value = false
  }
}

function closeForm() {
  isFormOpen.value = false
}

async function saveCategory() {
  isSaving.value = true
  formErrorText.value = ''
  fieldErrors.value = {}

  // Ô mô tả để trống thì gửi null, nghĩa là không có mô tả
  let description = form.description.trim()
  if (description === '') {
    description = null
  }
  const payload = {
    name: form.name,
    description: description,
  }

  try {
    if (editingCategoryId.value === null) {
      const responseBody = await createCategory(payload)
      showSuccess(`Đã thêm danh mục "${responseBody.data.name}"`)
    } else {
      const responseBody = await updateCategory(editingCategoryId.value, payload)
      showSuccess(`Đã lưu danh mục "${responseBody.data.name}"`)
    }
    isFormOpen.value = false
    loadCategories(pageInfo.value.page)
  } catch (error) {
    formErrorText.value = error.message
    fieldErrors.value = error.fieldErrors || {}
  } finally {
    isSaving.value = false
  }
}

async function confirmAndDeleteCategory(category) {
  const isConfirmed = window.confirm(
    `Xoá danh mục "${category.name}"?\nViệc này không hoàn tác được.`,
  )
  if (!isConfirmed) {
    return
  }

  try {
    await deleteCategory(category.id)
    showSuccess(`Đã xoá danh mục "${category.name}"`)

    // Xoá dòng cuối cùng của một trang thì trang đó trống, lùi về trang trước
    let pageNumber = pageInfo.value.page
    if (categories.value.length === 1 && pageNumber > 1) {
      pageNumber = pageNumber - 1
    }
    loadCategories(pageNumber)
  } catch (error) {
    showError(error.detailText)
  }
}

onMounted(() => {
  loadCategories(1)
})
</script>

<template>
  <section class="page">
    <header class="page-header">
      <div>
        <h1 class="page-title">Danh mục</h1>
        <p class="page-subtitle">Nhóm sản phẩm theo loại để dễ tìm và lọc</p>
      </div>

      <div v-if="isAdmin()" class="page-actions">
        <button type="button" class="button button-primary" @click="openCreateForm">
          <AppIcon name="plus" :size="16" />
          Thêm danh mục
        </button>
      </div>
      <span v-else class="view-only-pill">
        <AppIcon name="eye" :size="14" />
        Chỉ xem · cần quyền admin để sửa
      </span>
    </header>

    <div class="card data-card">
      <form class="data-toolbar" @submit.prevent="applySearch">
        <div class="input-icon-wrap toolbar-search">
          <AppIcon name="search" :size="16" />
          <input
            v-model.trim="searchText"
            class="input"
            type="search"
            placeholder="Tìm theo tên danh mục…"
            aria-label="Tìm theo tên danh mục"
          />
        </div>
        <div class="toolbar-actions">
          <button type="submit" class="button button-primary" :disabled="isLoading">Tìm</button>
          <button
            type="button"
            class="button button-ghost"
            :disabled="isLoading"
            @click="resetSearch"
          >
            <AppIcon name="rotate" :size="16" />
            Xoá tìm
          </button>
        </div>
      </form>

      <div v-if="errorText" class="alert alert-error data-card-alert">
        <AppIcon name="alert-circle" />
        <span>{{ errorText }}</span>
      </div>

      <div v-if="isLoading" class="loading-state">
        <span class="spinner"></span>
        Đang tải danh mục…
      </div>

      <div v-else-if="categories.length === 0" class="empty-state">
        <span class="empty-icon">
          <AppIcon name="tag" :size="24" />
        </span>
        <p v-if="appliedSearchText" class="empty-title">Không tìm thấy danh mục phù hợp</p>
        <p v-else class="empty-title">Chưa có danh mục nào</p>
        <p class="empty-text">Danh mục giúp gom các sản phẩm cùng loại.</p>
      </div>

      <div v-else class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>Danh mục</th>
              <th>Mô tả</th>
              <th v-if="isAdmin()" class="column-actions">
                <span class="visually-hidden">Thao tác</span>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="category in categories" :key="category.id">
              <td>
                <div class="entity">
                  <span class="entity-thumb" :class="pickToneClass(category.id)">
                    <AppIcon name="tag" :size="18" />
                  </span>
                  <div class="entity-text">
                    <div class="entity-name">{{ category.name }}</div>
                    <div class="entity-meta">#{{ category.id }}</div>
                  </div>
                </div>
              </td>
              <td>
                <span v-if="category.description" class="cell-description">
                  {{ category.description }}
                </span>
                <span v-else class="text-muted">—</span>
              </td>
              <td v-if="isAdmin()" class="column-actions">
                <div class="row-actions">
                  <button
                    type="button"
                    class="icon-button"
                    title="Sửa"
                    :aria-label="`Sửa ${category.name}`"
                    @click="openEditForm(category)"
                  >
                    <AppIcon name="pencil" :size="16" />
                  </button>
                  <button
                    type="button"
                    class="icon-button icon-button-danger"
                    title="Xoá"
                    :aria-label="`Xoá ${category.name}`"
                    @click="confirmAndDeleteCategory(category)"
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
          item-label="danh mục"
          @change-page="loadCategories"
        />
      </div>
    </div>

    <ModalDialog
      v-if="isFormOpen"
      :title="formTitle"
      subtitle="Ô có dấu * là bắt buộc"
      @close="closeForm"
    >
      <div v-if="isFormLoading" class="loading-state">
        <span class="spinner"></span>
        Đang tải danh mục…
      </div>

      <form v-else class="form" @submit.prevent="saveCategory">
        <div v-if="formErrorText" class="alert alert-error">
          <AppIcon name="alert-circle" />
          <span>{{ formErrorText }}</span>
        </div>

        <label class="form-field" :class="{ 'has-error': fieldErrors.name }">
          <span class="form-label">Tên danh mục <span class="required-mark">*</span></span>
          <input
            v-model.trim="form.name"
            class="input"
            type="text"
            maxlength="120"
            placeholder="Ví dụ: Áo, Quần, Phụ kiện"
            required
          />
          <span v-if="fieldErrors.name" class="field-error">{{ fieldErrors.name }}</span>
        </label>

        <label class="form-field" :class="{ 'has-error': fieldErrors.description }">
          <span class="form-label">Mô tả</span>
          <textarea
            v-model="form.description"
            class="input"
            rows="3"
            placeholder="Không bắt buộc"
          ></textarea>
          <span v-if="fieldErrors.description" class="field-error">
            {{ fieldErrors.description }}
          </span>
        </label>

        <div class="form-actions">
          <button type="button" class="button" @click="closeForm">Huỷ</button>
          <button type="submit" class="button button-primary" :disabled="isSaving">
            {{ isSaving ? 'Đang lưu…' : 'Lưu danh mục' }}
          </button>
        </div>
      </form>
    </ModalDialog>
  </section>
</template>
