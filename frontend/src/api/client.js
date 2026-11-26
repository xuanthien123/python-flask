// Ghép object thành chuỗi ?a=1&b=2, bỏ qua ô để trống.
// Phải bỏ ô trống vì gửi min_price= (rỗng) thì Flask báo 422: không phải số.
function buildQueryString(queryParams) {
  const searchParams = new URLSearchParams()

  for (const [key, value] of Object.entries(queryParams)) {
    if (value === '' || value === null || value === undefined) {
      continue
    }
    searchParams.append(key, value)
  }

  return searchParams.toString()
}

// Gom message và errors của Flask thành một câu để hiện cho người dùng.
// Lỗi 422 có thêm errors dạng { ten_o: ['lý do', ...] } nên ghép vào cho rõ sai ô nào.
function buildErrorText(responseBody) {
  let errorText = responseBody.message

  if (responseBody.errors) {
    const fieldMessages = []

    for (const [fieldName, reasons] of Object.entries(responseBody.errors)) {
      let reasonText
      if (Array.isArray(reasons)) {
        reasonText = reasons.join(', ')
      } else {
        reasonText = JSON.stringify(reasons)
      }
      fieldMessages.push(`${fieldName}: ${reasonText}`)
    }

    errorText = `${errorText} (${fieldMessages.join('; ')})`
  }

  return errorText
}

// Gọi một API GET của Flask.
// Flask luôn trả khung { success, data, message?, meta? }.
// Thành công: trả nguyên khung để trang tự lấy data và meta.
// Thất bại: ném lỗi, trang bắt bằng try/catch.
export async function getJson(path, queryParams = {}) {
  const queryString = buildQueryString(queryParams)

  let url = path
  if (queryString !== '') {
    url = `${path}?${queryString}`
  }

  // Gọi /api/... cùng địa chỉ với trang web, không ghi http://localhost:8080.
  // Lúc dev Vite chuyển tiếp sang nginx, lúc chạy thật nginx nhận luôn.
  const response = await fetch(url)

  let responseBody
  try {
    responseBody = await response.json()
  } catch {
    // Không đọc được JSON: thường là Flask hoặc nginx chưa chạy (lỗi 502, 504)
    throw new Error(`Không gọi được API (HTTP ${response.status})`)
  }

  if (!responseBody.success) {
    throw new Error(buildErrorText(responseBody))
  }

  return responseBody
}
