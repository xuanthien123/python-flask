import { deleteJson, downloadFile, getJson, postFile, postJson, putJson } from './client.js'

// filters: { q, category_id, min_price, max_price, sort, page, per_page }
// Kết quả: data là danh sách product của trang đó,
// meta là { page, per_page, total, pages } để vẽ phân trang.
export function fetchProductPage(filters) {
  return getJson('/api/products', filters)
}

// Kết quả: data là { total_products, total_quantity, total_inventory_value }
export function fetchProductSummary() {
  return getJson('/api/products/summary')
}

export function fetchProduct(productId) {
  return getJson(`/api/products/${productId}`)
}

// fields: { name, description, price, quantity, category_ids }
export function createProduct(fields) {
  return postJson('/api/products', fields)
}

// Gửi category_ids thì Flask thay toàn bộ category cũ của sản phẩm
export function updateProduct(productId, fields) {
  return putJson(`/api/products/${productId}`, fields)
}

export function deleteProduct(productId) {
  return deleteJson(`/api/products/${productId}`)
}

// Tải file Excel gồm mọi sản phẩm khớp bộ lọc (không chia trang)
export function downloadProductExport(filters) {
  return downloadFile('/api/products/export', filters, 'products.xlsx')
}

// File mẫu có sẵn danh sách category hiện có để chọn trong Excel
export function downloadImportTemplate() {
  return downloadFile('/api/products/import-template', {}, 'product_import_template.xlsx')
}

// Flask đọc file ở ô tên "file". Kết quả: data là { created_count }
export function importProductsFromExcel(excelFile) {
  return postFile('/api/products/import', 'file', excelFile)
}
