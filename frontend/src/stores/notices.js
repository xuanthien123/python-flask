import { reactive } from 'vue'

// Thông báo ngắn hiện ở góc trên bên phải rồi tự tắt.
// Lỗi để lâu hơn vì người dùng cần thời gian đọc lý do.
const SUCCESS_LIFETIME_MS = 3500
const ERROR_LIFETIME_MS = 7000

// Danh sách thông báo đang hiện. NoticeList.vue đọc danh sách này để vẽ.
export const notices = reactive([])

// Mỗi thông báo cần một id riêng để biết xoá cái nào
let nextNoticeId = 1

function addNotice(kind, text, lifetimeMs) {
  const notice = {
    id: nextNoticeId,
    kind: kind,
    text: text,
  }
  nextNoticeId = nextNoticeId + 1

  notices.push(notice)

  // setTimeout: chờ lifetimeMs mili giây rồi mới chạy hàm bên trong
  setTimeout(() => {
    removeNotice(notice.id)
  }, lifetimeMs)
}

export function removeNotice(noticeId) {
  const noticeIndex = notices.findIndex((notice) => notice.id === noticeId)

  // Người dùng đã bấm tắt trước khi hết giờ thì lúc hết giờ không còn gì để xoá
  if (noticeIndex === -1) {
    return
  }

  notices.splice(noticeIndex, 1)
}

export function showSuccess(text) {
  addNotice('success', text, SUCCESS_LIFETIME_MS)
}

export function showError(text) {
  addNotice('error', text, ERROR_LIFETIME_MS)
}
