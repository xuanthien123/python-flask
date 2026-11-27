import { deleteJson, getJson, postJson, putJson } from './client.js'

// Flask cho tối đa 100 dòng mỗi trang
const MAX_CATEGORIES_PER_PAGE = 100

// filters: { q, page, per_page }
// Kết quả: data là danh sách category của trang đó, meta là { page, per_page, total, pages }
export function fetchCategoryPage(filters) {
  return getJson('/api/categories', filters)
}

// Lấy hết category để làm ô chọn (lọc sản phẩm, gán category cho sản phẩm).
// Mỗi lần chỉ lấy được 100 dòng nên gọi lần lượt từng trang tới trang cuối.
// Kết quả: mảng category, không phải khung { success, data } như các hàm khác.
export async function fetchAllCategories() {
  const allCategories = []
  let pageNumber = 1
  let lastPage = 1

  while (pageNumber <= lastPage) {
    const responseBody = await getJson('/api/categories', {
      page: pageNumber,
      per_page: MAX_CATEGORIES_PER_PAGE,
    })

    for (const category of responseBody.data) {
      allCategories.push(category)
    }

    lastPage = responseBody.meta.pages
    pageNumber = pageNumber + 1
  }

  return allCategories
}

export function fetchCategory(categoryId) {
  return getJson(`/api/categories/${categoryId}`)
}

// fields: { name, description }
export function createCategory(fields) {
  return postJson('/api/categories', fields)
}

export function updateCategory(categoryId, fields) {
  return putJson(`/api/categories/${categoryId}`, fields)
}

// Flask từ chối (409) nếu category còn sản phẩm
export function deleteCategory(categoryId) {
  return deleteJson(`/api/categories/${categoryId}`)
}
