import { clearSession, saveAccessToken, session } from '../stores/session.js'

// Flask trả câu báo lỗi tiếng Anh. Câu nào biết trước thì đổi sang tiếng Việt
// cho người dùng dễ hiểu; câu lạ thì giữ nguyên tiếng Anh.
const MESSAGE_TRANSLATIONS = {
  // Câu báo chung (message)
  'Invalid email or password': 'Email hoặc mật khẩu không đúng',
  'Validation failed': 'Dữ liệu chưa hợp lệ, xem lại các ô báo đỏ',
  'Authentication required': 'Bạn cần đăng nhập để làm việc này',
  'Invalid token': 'Phiên đăng nhập không hợp lệ, hãy đăng nhập lại',
  'Token has been revoked': 'Phiên đăng nhập đã kết thúc, hãy đăng nhập lại',
  'Token expired': 'Phiên đăng nhập đã hết hạn, hãy đăng nhập lại',
  'Forbidden – insufficient role': 'Bạn không có quyền làm việc này (cần tài khoản admin)',
  'User not found': 'Không tìm thấy tài khoản',
  'Category name already exists': 'Tên danh mục này đã có',
  'Category still has products': 'Danh mục còn sản phẩm nên chưa xoá được',
  'Category not found': 'Không tìm thấy danh mục',
  'Product not found': 'Không tìm thấy sản phẩm',
  'Current password is incorrect': 'Mật khẩu hiện tại không đúng',
  'New password must differ from the current one': 'Mật khẩu mới phải khác mật khẩu hiện tại',
  'Invalid or expired reset token': 'Link đặt lại mật khẩu sai, đã dùng rồi hoặc đã hết hạn',
  'Invalid refresh token': 'Phiên đăng nhập không hợp lệ',
  'No fields to update': 'Chưa có gì thay đổi để lưu',
  'Provide at least one field to update': 'Chưa có gì thay đổi để lưu',
  'Internal server error': 'Máy chủ gặp lỗi, thử lại sau',
  'min_price must not be greater than max_price': '"Giá từ" không được lớn hơn "Giá đến"',
  // Lý do từng ô do marshmallow sinh ra (nằm trong errors)
  'Missing data for required field.': 'Ô này bắt buộc',
  'Field may not be null.': 'Ô này bắt buộc',
  'Not a valid email address.': 'Email không hợp lệ',
  'Not a valid number.': 'Phải là số',
  'Not a valid integer.': 'Phải là số nguyên',
  'Not a valid date.': 'Ngày không hợp lệ',
  'Must be greater than or equal to 0.': 'Phải từ 0 trở lên',
  'Shorter than minimum length 8.': 'Cần ít nhất 8 ký tự',
  'Length must be between 1 and 120.': 'Cần từ 1 đến 120 ký tự',
  'Length must be between 1 and 255.': 'Cần từ 1 đến 255 ký tự',
  // Lỗi file khi nhập Excel
  'File must be an .xlsx workbook': 'File phải là file Excel .xlsx',
  'Sheet "Products" not found': 'Trong file không có sheet "Products". Hãy dùng file mẫu.',
  'No products to import': 'File chưa có sản phẩm nào để nhập',
  'At most 1000 products per file': 'Mỗi file chỉ nhập được tối đa 1000 sản phẩm',
}

// Tên ô Flask dùng trong lỗi 422, đổi sang tên ô người dùng thấy trên màn hình
const FIELD_LABELS = {
  name: 'Tên',
  description: 'Mô tả',
  price: 'Giá',
  quantity: 'Số lượng',
  category_id: 'Danh mục',
  category_ids: 'Danh mục',
  min_price: 'Giá từ',
  max_price: 'Giá đến',
  sort: 'Sắp xếp',
  email: 'Email',
  password: 'Mật khẩu',
  current_password: 'Mật khẩu hiện tại',
  new_password: 'Mật khẩu mới',
  token: 'Mã đặt lại',
  address: 'Địa chỉ',
  date_of_birth: 'Ngày sinh',
  sex: 'Giới tính',
  file: 'File',
}

function translateMessage(message) {
  const translatedMessage = MESSAGE_TRANSLATIONS[message]
  if (translatedMessage === undefined) {
    return message
  }
  return translatedMessage
}

function readFieldLabel(fieldName) {
  const fieldLabel = FIELD_LABELS[fieldName]
  if (fieldLabel === undefined) {
    return fieldName
  }
  return fieldLabel
}

// reasons là danh sách lý do của một ô, ví dụ ['Not a valid number.'].
// Dịch từng lý do rồi nối lại thành một câu.
export function translateReasons(reasons) {
  const translatedReasons = reasons.map((reason) => translateMessage(reason))
  return translatedReasons.join(', ')
}

function isListOfTexts(value) {
  if (!Array.isArray(value)) {
    return false
  }
  for (const listItem of value) {
    if (typeof listItem !== 'string') {
      return false
    }
  }
  return true
}

// Đổi errors của Flask { ten_o: ['lý do 1', 'lý do 2'] } thành { ten_o: 'lý do 1, lý do 2' }
// đã dịch, để trang chỉ việc in ra dưới ô nhập.
// Giá trị không phải danh sách chữ (ví dụ lỗi từng dòng khi nhập Excel) thì giữ nguyên.
function buildFieldErrors(rawErrors) {
  const fieldErrors = {}
  if (!rawErrors) {
    return fieldErrors
  }

  for (const [fieldName, reasons] of Object.entries(rawErrors)) {
    if (isListOfTexts(reasons)) {
      fieldErrors[fieldName] = translateReasons(reasons)
    } else {
      fieldErrors[fieldName] = reasons
    }
  }
  return fieldErrors
}

// Câu đầy đủ để hiện ở chỗ không có ô nhập (thông báo góc màn hình, khung lỗi trên bảng):
// câu chính kèm lý do từng ô, ví dụ "Dữ liệu chưa hợp lệ (Giá từ: Phải là số)".
function buildDetailText(message, fieldErrors) {
  const fieldMessages = []

  for (const [fieldName, reasonText] of Object.entries(fieldErrors)) {
    // _schema đã được đưa vào câu chính, bỏ qua để không lặp
    if (fieldName === '_schema') {
      continue
    }
    if (typeof reasonText !== 'string') {
      continue
    }
    const fieldLabel = readFieldLabel(fieldName)
    fieldMessages.push(`${fieldLabel}: ${reasonText}`)
  }

  if (fieldMessages.length === 0) {
    return message
  }
  return `${message} (${fieldMessages.join('; ')})`
}

// Tạo lỗi từ body lỗi của Flask { success: false, message, code?, errors? }.
// Ngoài message, lỗi mang thêm:
//   status: mã HTTP (401, 404, 422...)
//   code: mã lỗi token của Flask (token_expired...), có thể không có
//   fieldErrors: lý do từng ô, để form in dưới đúng ô
//   detailText: câu đầy đủ kèm lý do từng ô, để hiện ở chỗ không có form
function buildApiError(responseBody, status) {
  const fieldErrors = buildFieldErrors(responseBody.errors)

  let message = translateMessage(responseBody.message)
  // Lỗi của cả form (không thuộc ô nào) Flask để ở key _schema, câu này cụ thể hơn "Validation failed"
  if (typeof fieldErrors._schema === 'string') {
    message = fieldErrors._schema
  }

  const error = new Error(message)
  error.status = status
  error.code = responseBody.code
  error.fieldErrors = fieldErrors
  error.detailText = buildDetailText(message, fieldErrors)
  return error
}

function buildSimpleError(message, status) {
  return buildApiError({ message: message }, status)
}

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

// Gửi một request tới Flask, chưa đọc kết quả.
// options có thể có:
//   method: 'GET' (mặc định), 'POST', 'PUT', 'DELETE'
//   query: object để ghép thành ?a=1&b=2
//   jsonBody: object gửi đi dạng JSON
//   formData: dùng khi gửi file
//   token: token muốn gửi thay cho access token (dùng khi gọi /refresh)
async function sendOnce(path, options) {
  let method = 'GET'
  if (options.method) {
    method = options.method
  }

  // Gọi /api/... cùng địa chỉ với trang web, không ghi http://localhost:8080.
  // Lúc dev Vite chuyển tiếp sang nginx, lúc chạy thật nginx nhận luôn.
  let url = path
  if (options.query) {
    const queryString = buildQueryString(options.query)
    if (queryString !== '') {
      url = `${path}?${queryString}`
    }
  }

  const headers = {}

  // Đã đăng nhập thì gửi kèm access token để Flask biết ai đang gọi
  let token = session.accessToken
  if (options.token) {
    token = options.token
  }
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  let body = undefined
  if (options.formData) {
    // Gửi file thì không tự đặt Content-Type. Trình duyệt sẽ tự ghi multipart/form-data
    // kèm chuỗi ngăn cách (boundary), Flask cần chuỗi này để tách file ra.
    body = options.formData
  } else if (options.jsonBody !== undefined) {
    headers['Content-Type'] = 'application/json'
    body = JSON.stringify(options.jsonBody)
  }

  try {
    const response = await fetch(url, {
      method: method,
      headers: headers,
      body: body,
    })
    return response
  } catch {
    // fetch chỉ ném lỗi khi không nối được tới máy chủ (mất mạng, nginx chưa chạy)
    throw buildSimpleError('Không kết nối được máy chủ, thử lại sau', 0)
  }
}

// Đọc code trong body lỗi (ví dụ token_expired) mà vẫn giữ body cho bước sau đọc tiếp.
// Body của response chỉ đọc được một lần, nên đọc trên bản sao (clone).
async function readErrorCode(response) {
  try {
    const copiedResponse = response.clone()
    const responseBody = await copiedResponse.json()
    return responseBody.code
  } catch {
    return undefined
  }
}

// Xin access token mới bằng refresh token (refresh token sống 30 ngày).
// Flask không thu hồi refresh token khi gọi /refresh, nên lỡ hai request
// cùng hết hạn một lúc và cùng xin token mới thì vẫn không sao.
async function requestNewAccessToken() {
  if (!session.refreshToken) {
    return false
  }

  try {
    const response = await sendOnce('/api/auth/refresh', {
      method: 'POST',
      token: session.refreshToken,
    })
    if (!response.ok) {
      return false
    }
    const responseBody = await response.json()
    saveAccessToken(responseBody.data.access_token)
    return true
  } catch {
    return false
  }
}

// Phiên không dùng được nữa (refresh token cũng hết hạn, hoặc token đã bị thu hồi):
// xoá phiên rồi đưa về trang đăng nhập.
// Dùng window.location để tải lại hẳn trang, khỏi phải gọi router từ file này.
function endExpiredSession() {
  clearSession()
  window.location.assign('/login?expired=1')
}

// Gửi request, và tự lo chuyện token hết hạn:
// access token chỉ sống 30 phút, hết hạn thì Flask trả 401 kèm code token_expired.
// Lúc đó xin token mới bằng refresh token rồi gửi lại đúng request đó một lần.
async function sendWithLogin(path, options) {
  const response = await sendOnce(path, options)

  if (response.status !== 401) {
    return response
  }

  // Chưa đăng nhập thì 401 là lỗi bình thường (ví dụ sai mật khẩu), trả về để trang báo lỗi
  if (!session.accessToken) {
    return response
  }

  const errorCode = await readErrorCode(response)

  if (errorCode === 'token_expired') {
    const isRefreshed = await requestNewAccessToken()
    if (isRefreshed) {
      const retriedResponse = await sendOnce(path, options)
      return retriedResponse
    }
    endExpiredSession()
  }

  if (errorCode === 'token_revoked' || errorCode === 'token_invalid') {
    endExpiredSession()
  }

  return response
}

// Flask luôn trả khung { success, data, message?, meta? }.
// Thành công: trả nguyên khung để trang tự lấy data và meta.
// Thất bại: ném lỗi, trang bắt bằng try/catch.
async function readEnvelope(response) {
  let responseBody
  try {
    responseBody = await response.json()
  } catch {
    // Không đọc được JSON: thường là Flask hoặc nginx chưa chạy (lỗi 502, 504)
    throw buildSimpleError(`Không gọi được API (HTTP ${response.status})`, response.status)
  }

  if (!responseBody.success) {
    throw buildApiError(responseBody, response.status)
  }

  return responseBody
}

export async function getJson(path, queryParams = {}) {
  const response = await sendWithLogin(path, { query: queryParams })
  return readEnvelope(response)
}

export async function postJson(path, jsonBody = {}) {
  const response = await sendWithLogin(path, { method: 'POST', jsonBody: jsonBody })
  return readEnvelope(response)
}

export async function putJson(path, jsonBody) {
  const response = await sendWithLogin(path, { method: 'PUT', jsonBody: jsonBody })
  return readEnvelope(response)
}

export async function deleteJson(path) {
  const response = await sendWithLogin(path, { method: 'DELETE' })
  return readEnvelope(response)
}

// Gửi một file lên Flask. fieldName là tên ô Flask đọc (request.files.get(...))
export async function postFile(path, fieldName, file) {
  // FormData: giống form HTML có ô chọn file, trình duyệt gửi dạng multipart/form-data
  const formData = new FormData()
  formData.append(fieldName, file)

  const response = await sendWithLogin(path, { method: 'POST', formData: formData })
  return readEnvelope(response)
}

// Flask gửi tên file trong header, ví dụ: attachment; filename=products_20261126.xlsx
function readFilenameFromHeader(response) {
  const disposition = response.headers.get('Content-Disposition')
  if (!disposition) {
    return null
  }

  // Lấy phần chữ sau "filename=", bỏ dấu ngoặc kép nếu có
  const match = disposition.match(/filename="?([^";]+)"?/)
  if (!match) {
    return null
  }
  return match[1]
}

// Bắt trình duyệt lưu file: tạo một link tạm trỏ tới file rồi tự bấm vào link đó
function saveBlobAsFile(fileBlob, filename) {
  const blobUrl = URL.createObjectURL(fileBlob)

  const link = document.createElement('a')
  link.href = blobUrl
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()

  // Chờ một chút cho trình duyệt bắt đầu tải rồi mới giải phóng bộ nhớ của file
  setTimeout(() => {
    URL.revokeObjectURL(blobUrl)
  }, 1000)
}

// Tải file từ API cần đăng nhập (xuất Excel, file mẫu).
// Không dùng <a href> thường được vì link thường không gửi kèm token được,
// nên tải bằng fetch rồi tự lưu file.
export async function downloadFile(path, queryParams, fallbackFilename) {
  const response = await sendWithLogin(path, { query: queryParams })

  if (!response.ok) {
    // Lỗi thì Flask vẫn trả JSON có message, readEnvelope đọc ra rồi ném lỗi
    await readEnvelope(response)
    throw buildSimpleError(`Không tải được file (HTTP ${response.status})`, response.status)
  }

  const fileBlob = await response.blob()

  let filename = readFilenameFromHeader(response)
  if (!filename) {
    filename = fallbackFilename
  }

  saveBlobAsFile(fileBlob, filename)
}
