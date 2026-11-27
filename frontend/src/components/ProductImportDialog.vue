<script setup>
// Hộp thoại nhập nhiều sản phẩm cùng lúc từ file Excel
import { ref } from 'vue'

import { translateReasons } from '../api/client.js'
import { downloadImportTemplate, importProductsFromExcel } from '../api/products.js'
import { showError } from '../stores/notices.js'
import AppIcon from './AppIcon.vue'
import ModalDialog from './ModalDialog.vue'

// close: bấm Huỷ hoặc ✕. imported: nhập xong, gửi kèm số sản phẩm đã tạo
const emit = defineEmits(['close', 'imported'])

// ref gắn vào ô chọn file, để xoá file đã chọn khi cần chọn lại
const fileInput = ref(null)
const selectedFile = ref(null)
// true khi đang kéo file ngang qua ô thả file, để tô màu ô đó
const isDraggingFile = ref(false)
const isUploading = ref(false)
const isDownloadingTemplate = ref(false)
const errorText = ref('')
// Mỗi phần tử: { row: số dòng trong Excel, text: lý do lỗi }
const rowErrors = ref([])

function chooseFile(file) {
  selectedFile.value = file
  errorText.value = ''
  rowErrors.value = []
}

function rememberSelectedFile(event) {
  // event.target là ô chọn file, files là các file đã chọn; chỉ cần file đầu tiên
  const fileList = event.target.files
  if (fileList.length === 0) {
    selectedFile.value = null
    return
  }
  chooseFile(fileList[0])
}

function takeDroppedFile(event) {
  isDraggingFile.value = false

  // dataTransfer.files: các file người dùng vừa kéo thả vào
  const fileList = event.dataTransfer.files
  if (fileList.length === 0) {
    return
  }
  chooseFile(fileList[0])
}

async function downloadTemplate() {
  isDownloadingTemplate.value = true
  try {
    await downloadImportTemplate()
  } catch (error) {
    showError(error.detailText)
  } finally {
    isDownloadingTemplate.value = false
  }
}

// Flask trả lỗi từng dòng dạng: [{ row: 3, errors: { price: ['Not a valid number.'] } }]
// Đổi thành: [{ row: 3, text: 'price: Phải là số' }] để in ra danh sách.
// Giữ tên cột tiếng Anh vì file Excel cũng dùng đúng tên cột đó.
function buildRowErrorLines(rawRowErrors) {
  const lines = []

  for (const rowError of rawRowErrors) {
    const reasonParts = []

    for (const [columnName, reasons] of Object.entries(rowError.errors)) {
      let reasonText
      if (Array.isArray(reasons)) {
        reasonText = translateReasons(reasons)
      } else {
        reasonText = JSON.stringify(reasons)
      }
      reasonParts.push(`${columnName}: ${reasonText}`)
    }

    lines.push({ row: rowError.row, text: reasonParts.join('; ') })
  }

  return lines
}

function clearSelectedFile() {
  // Bắt chọn lại file sau khi sửa: trình duyệt không báo đổi nếu chọn lại đúng file cũ,
  // và file đã sửa trên máy cần được đọc lại từ đầu
  selectedFile.value = null
  fileInput.value.value = ''
}

async function uploadSelectedFile() {
  isUploading.value = true
  errorText.value = ''
  rowErrors.value = []

  try {
    const responseBody = await importProductsFromExcel(selectedFile.value)
    emit('imported', responseBody.data.created_count)
  } catch (error) {
    const fieldErrors = error.fieldErrors || {}

    if (Array.isArray(fieldErrors.rows)) {
      // Chỉ cần một dòng lỗi là Flask không nhập dòng nào, nên phải nói rõ cho người dùng
      rowErrors.value = buildRowErrorLines(fieldErrors.rows)
      errorText.value = `Chưa nhập sản phẩm nào vì file có ${rowErrors.value.length} dòng lỗi. Sửa các dòng dưới đây rồi chọn lại file:`
    } else if (typeof fieldErrors.file === 'string') {
      errorText.value = fieldErrors.file
    } else {
      errorText.value = error.message
    }

    clearSelectedFile()
  } finally {
    isUploading.value = false
  }
}
</script>

<template>
  <ModalDialog
    title="Nhập sản phẩm từ Excel"
    subtitle="Thêm nhiều sản phẩm cùng lúc bằng file mẫu"
    @close="emit('close')"
  >
    <ol class="steps">
      <li class="step">
        <span class="step-number">1</span>
        <div class="step-content">
          <p class="step-title">Tải file mẫu và điền sản phẩm</p>
          <p class="step-text">
            Điền vào sheet <strong>Products</strong>, mỗi dòng một sản phẩm. Cột tiêu đề màu vàng
            là bắt buộc, tối đa 1000 dòng.
          </p>
          <div>
            <button
              type="button"
              class="button button-small"
              :disabled="isDownloadingTemplate"
              @click="downloadTemplate"
            >
              <AppIcon name="download" :size="16" />
              {{ isDownloadingTemplate ? 'Đang tải…' : 'Tải file mẫu' }}
            </button>
          </div>
        </div>
      </li>
      <li class="step">
        <span class="step-number">2</span>
        <div class="step-content">
          <p class="step-title">Chọn file đã điền</p>
          <!-- Bấm vào cả khung là mở hộp chọn file, vì ô chọn file nằm trong <label>.
               .prevent ở dragover, drop: chặn trình duyệt tự mở file ra xem khi thả vào. -->
          <label
            class="dropzone"
            :class="{ 'dropzone-active': isDraggingFile, 'dropzone-filled': selectedFile }"
            @dragover.prevent="isDraggingFile = true"
            @dragleave="isDraggingFile = false"
            @drop.prevent="takeDroppedFile"
          >
            <input
              ref="fileInput"
              class="visually-hidden"
              type="file"
              accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
              @change="rememberSelectedFile"
            />
            <AppIcon name="file-spreadsheet" :size="28" />
            <span v-if="selectedFile" class="dropzone-file">{{ selectedFile.name }}</span>
            <span v-else>Bấm để chọn file <strong>.xlsx</strong> hoặc kéo thả vào đây</span>
          </label>
        </div>
      </li>
    </ol>

    <div v-if="errorText" class="alert alert-error">
      <AppIcon name="alert-circle" />
      <div class="alert-content">
        <p>{{ errorText }}</p>
        <ul v-if="rowErrors.length > 0" class="row-error-list">
          <li v-for="rowError in rowErrors" :key="rowError.row">
            <strong>Dòng {{ rowError.row }}:</strong> {{ rowError.text }}
          </li>
        </ul>
      </div>
    </div>

    <div class="form-actions">
      <button type="button" class="button" @click="emit('close')">Huỷ</button>
      <button
        type="button"
        class="button button-primary"
        :disabled="isUploading || selectedFile === null"
        @click="uploadSelectedFile"
      >
        <AppIcon name="upload" :size="16" />
        {{ isUploading ? 'Đang nhập…' : 'Nhập sản phẩm' }}
      </button>
    </div>
  </ModalDialog>
</template>
