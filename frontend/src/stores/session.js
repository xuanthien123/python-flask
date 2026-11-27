import { reactive } from 'vue'

// Tên các ô lưu trong localStorage của trình duyệt.
// localStorage giữ dữ liệu cả khi tắt trình duyệt, nên mở lại trang vẫn còn đăng nhập.
const ACCESS_TOKEN_KEY = 'access_token'
const REFRESH_TOKEN_KEY = 'refresh_token'
const USER_KEY = 'current_user'

const ADMIN_ROLE = 'admin'

function readSavedUser() {
  const savedText = localStorage.getItem(USER_KEY)
  if (savedText === null) {
    return null
  }

  try {
    return JSON.parse(savedText)
  } catch {
    // Chuỗi đã lưu bị hỏng thì coi như chưa có thông tin user
    return null
  }
}

// Phiên đăng nhập dùng chung cho cả app.
// reactive: trang nào đọc session.user thì tự vẽ lại khi đăng nhập hay đăng xuất.
// localStorage.getItem trả null khi chưa lưu gì, nghĩa là chưa đăng nhập.
export const session = reactive({
  accessToken: localStorage.getItem(ACCESS_TOKEN_KEY),
  refreshToken: localStorage.getItem(REFRESH_TOKEN_KEY),
  user: readSavedUser(),
})

// loginData là data của API đăng nhập: { access_token, refresh_token, user, ... }
export function saveLogin(loginData) {
  // Ghi vào session để giao diện đổi ngay
  session.accessToken = loginData.access_token
  session.refreshToken = loginData.refresh_token

  // Ghi vào localStorage để tải lại trang vẫn còn
  localStorage.setItem(ACCESS_TOKEN_KEY, loginData.access_token)
  localStorage.setItem(REFRESH_TOKEN_KEY, loginData.refresh_token)

  saveUser(loginData.user)
}

// Gọi khi xin được access token mới bằng refresh token
export function saveAccessToken(accessToken) {
  session.accessToken = accessToken
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken)
}

export function saveUser(user) {
  session.user = user

  // localStorage chỉ lưu được chữ, nên đổi object thành chuỗi JSON trước khi lưu
  const userText = JSON.stringify(user)
  localStorage.setItem(USER_KEY, userText)
}

export function clearSession() {
  session.accessToken = null
  session.refreshToken = null
  session.user = null

  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

export function isLoggedIn() {
  return session.accessToken !== null
}

// Chỉ dùng để ẩn, hiện nút trên giao diện.
// Quyền thật vẫn do Flask kiểm ở mỗi API, sửa localStorage cũng không qua được.
export function isAdmin() {
  if (session.user === null) {
    return false
  }
  return session.user.roles.includes(ADMIN_ROLE)
}
