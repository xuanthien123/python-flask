import { getJson } from './client.js'

// filters: { q, min_price, max_price, sort, page, per_page }
// Kết quả: data là danh sách product của trang đó,
// meta là { page, per_page, total, pages } để vẽ phân trang.
export function fetchProductPage(filters) {
  return getJson('/api/products', filters)
}

// Kết quả: data là { total_products, total_quantity, total_inventory_value }
export function fetchProductSummary() {
  return getJson('/api/products/summary')
}
