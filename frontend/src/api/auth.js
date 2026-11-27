import { getJson, postJson, putJson } from './client.js'

// Kết quả: data là { access_token, refresh_token, token_type, expires_in, user }
export function login(email, password) {
  return postJson('/api/auth/login', {
    email: email,
    password: password,
  })
}

// Flask luôn trả thành công, kể cả email chưa đăng ký,
// để người lạ không dò được email nào có tài khoản
export function requestPasswordReset(email) {
  return postJson('/api/auth/forgot-password', { email: email })
}

// resetToken lấy từ link trong mail (phần ?token=...)
export function resetPassword(resetToken, newPassword) {
  return postJson('/api/auth/reset-password', {
    token: resetToken,
    new_password: newPassword,
  })
}

// Kết quả: data là { id, name, email, roles, address, date_of_birth, sex, email_verified_at }
export function fetchCurrentUser() {
  return getJson('/api/auth/me')
}

export function logout(refreshToken) {
  // Gửi kèm refresh token để Flask thu hồi luôn token này, không chỉ access token
  const body = {}
  if (refreshToken) {
    body.refresh_token = refreshToken
  }
  return postJson('/api/auth/logout', body)
}

export function changePassword(currentPassword, newPassword) {
  return putJson('/api/auth/password', {
    current_password: currentPassword,
    new_password: newPassword,
  })
}

// fields: { name, address, date_of_birth, sex }. Gửi field nào thì Flask sửa field đó.
export function updateProfile(fields) {
  return putJson('/api/auth/update-profile', fields)
}
