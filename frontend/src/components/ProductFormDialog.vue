<script setup>
// Hộp thoại thêm mới hoặc sửa một sản phẩm
import { computed, onMounted, reactive, ref } from 'vue'

import { createProduct, fetchProduct, updateProduct } from '../api/products.js'
import AppIcon from './AppIcon.vue'
import ModalDialog from './ModalDialog.vue'

const props = defineProps({
  // null là thêm mới, có số là sửa sản phẩm có id đó
  productId: { type: Number, default: null },
  // Mọi danh mục để tick chọn, trang cha đã tải sẵn
  categories: { type: Array, required: true },
})

// close: bấm Huỷ hoặc ✕. saved: lưu xong, gửi kèm sản phẩm vừa lưu
const emit = defineEmits(['close', 'saved'])

const isEditing = computed(() => props.productId !== null)

const dialogTitle = computed(() => {
  if (isEditing.value) {
    return 'Sửa sản phẩm'
  }
  return 'Thêm sản phẩm'
})

const dialogSubtitle = computed(() => {
  if (isEditing.value) {
    return 'Đổi thông tin rồi bấm Lưu'
  }
  return 'Ô có dấu * là bắt buộc'
})

const form = reactive({
  name: '',
  description: '',
  price: '',
  quantity: 0,
  categoryIds: [],
})

// Sửa thì phải tải sản phẩm trước, nên bắt đầu ở trạng thái đang tải luôn.
// Để false rồi mới đổi sau thì form trống sẽ chớp lên một chút trước khi có dữ liệu.
const isLoading = ref(isEditing.value)
const isSaving = ref(false)
const errorText = ref('')
const fieldErrors = ref({})

async function loadProduct() {
  try {
    // Lấy bản mới nhất từ máy chủ, phòng khi ai đó vừa sửa sản phẩm này
    const responseBody = await fetchProduct(props.productId)
    const product = responseBody.data

    form.name = product.name
    form.price = product.price
    form.quantity = product.quantity

    // Sản phẩm không có mô tả thì Flask trả null, ô nhập cần chuỗi rỗng
    if (product.description === null) {
      form.description = ''
    } else {
      form.description = product.description
    }

    // Ô tick chọn danh mục chỉ cần danh sách id
    form.categoryIds = product.categories.map((category) => category.id)
  } catch (error) {
    errorText.value = error.message
  } finally {
    isLoading.value = false
  }
}

function buildProductPayload() {
  // Ô mô tả để trống thì gửi null, nghĩa là sản phẩm không có mô tả
  let description = form.description.trim()
  if (description === '') {
    description = null
  }

  return {
    name: form.name,
    description: description,
    // Ô type="number" có thể trả về chuỗi, đổi hẳn sang số cho chắc
    price: Number(form.price),
    quantity: Number(form.quantity),
    category_ids: form.categoryIds,
  }
}

async function saveProduct() {
  isSaving.value = true
  errorText.value = ''
  fieldErrors.value = {}

  const payload = buildProductPayload()

  try {
    let responseBody
    if (isEditing.value) {
      responseBody = await updateProduct(props.productId, payload)
    } else {
      responseBody = await createProduct(payload)
    }
    emit('saved', responseBody.data)
  } catch (error) {
    errorText.value = error.message
    fieldErrors.value = error.fieldErrors || {}
  } finally {
    isSaving.value = false
  }
}

onMounted(() => {
  if (isEditing.value) {
    loadProduct()
  }
})
</script>

<template>
  <ModalDialog :title="dialogTitle" :subtitle="dialogSubtitle" @close="emit('close')">
    <div v-if="isLoading" class="loading-state">
      <span class="spinner"></span>
      Đang tải sản phẩm…
    </div>

    <!-- .prevent: chặn trình duyệt tải lại cả trang khi bấm Lưu hoặc Enter -->
    <form v-else class="form" @submit.prevent="saveProduct">
      <div v-if="errorText" class="alert alert-error">
        <AppIcon name="alert-circle" />
        <span>{{ errorText }}</span>
      </div>

      <label class="form-field" :class="{ 'has-error': fieldErrors.name }">
        <span class="form-label">Tên sản phẩm <span class="required-mark">*</span></span>
        <input
          v-model.trim="form.name"
          class="input"
          type="text"
          maxlength="255"
          placeholder="Ví dụ: Áo thun cotton"
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
        <span v-if="fieldErrors.description" class="field-error">{{ fieldErrors.description }}</span>
      </label>

      <div class="form-row">
        <label class="form-field" :class="{ 'has-error': fieldErrors.price }">
          <span class="form-label">Giá <span class="required-mark">*</span></span>
          <!-- step="any": cho nhập số lẻ như 19.99 -->
          <input
            v-model="form.price"
            class="input"
            type="number"
            min="0"
            step="any"
            placeholder="0"
            required
          />
          <span v-if="fieldErrors.price" class="field-error">{{ fieldErrors.price }}</span>
        </label>

        <label class="form-field" :class="{ 'has-error': fieldErrors.quantity }">
          <span class="form-label">Số lượng trong kho</span>
          <!-- step="1": chỉ cho số nguyên, vì Flask từ chối số lẻ như 2.5 -->
          <input v-model="form.quantity" class="input" type="number" min="0" step="1" />
          <span v-if="fieldErrors.quantity" class="field-error">{{ fieldErrors.quantity }}</span>
        </label>
      </div>

      <!-- fieldset + legend: gom nhóm ô tick dưới một tiêu đề -->
      <fieldset class="form-field" :class="{ 'has-error': fieldErrors.category_ids }">
        <legend class="form-label">Danh mục</legend>
        <p v-if="categories.length === 0" class="form-hint">
          Chưa có danh mục nào. Tạo ở trang Danh mục trước.
        </p>
        <div v-else class="checkbox-list">
          <label v-for="category in categories" :key="category.id" class="checkbox-item">
            <!-- v-model với mảng: tick thì id được thêm vào form.categoryIds, bỏ tick thì bị gỡ ra -->
            <input v-model="form.categoryIds" type="checkbox" :value="category.id" />
            <span>{{ category.name }}</span>
          </label>
        </div>
        <span v-if="fieldErrors.category_ids" class="field-error">
          {{ fieldErrors.category_ids }}
        </span>
      </fieldset>

      <div class="form-actions">
        <button type="button" class="button" @click="emit('close')">Huỷ</button>
        <button type="submit" class="button button-primary" :disabled="isSaving">
          {{ isSaving ? 'Đang lưu…' : 'Lưu sản phẩm' }}
        </button>
      </div>
    </form>
  </ModalDialog>
</template>
