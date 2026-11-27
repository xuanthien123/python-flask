// /health nằm ngoài /api và không dùng khung { success, data },
// nên gọi thẳng fetch, không đi qua client.js.
// Kết quả: { isHealthy, detailText }, detailText để hiện khi rê chuột vào chấm trạng thái.
export async function checkApiHealth() {
  try {
    const response = await fetch('/health')
    const responseBody = await response.json()

    if (responseBody.status === 'ok') {
      return { isHealthy: true, detailText: 'API và database đang chạy' }
    }
    return { isHealthy: false, detailText: `Database lỗi: ${responseBody.db}` }
  } catch {
    return { isHealthy: false, detailText: 'Không gọi được API' }
  }
}
