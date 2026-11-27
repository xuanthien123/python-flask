import { createRouter, createWebHistory } from 'vue-router'

import AccountPage from '../pages/AccountPage.vue'
import CategoryListPage from '../pages/CategoryListPage.vue'
import ForgotPasswordPage from '../pages/ForgotPasswordPage.vue'
import LoginPage from '../pages/LoginPage.vue'
import ProductListPage from '../pages/ProductListPage.vue'
import ResetPasswordPage from '../pages/ResetPasswordPage.vue'
import { isLoggedIn } from '../stores/session.js'

const APP_NAME = 'Product Manager'
// Trang mở ra sau khi đăng nhập, khi không có trang nào khác đang chờ
const HOME_PATH = '/products'

// Mỗi dòng: URL nào thì hiện trang (component) nào.
// Thêm trang mới: tạo file trong src/pages rồi thêm một dòng ở đây.
// meta là thông tin thêm của trang:
//   title: chữ hiện trên tab trình duyệt
//   public: vào được khi chưa đăng nhập. Trang không có public thì phải đăng nhập trước.
//   guestOnly: đã đăng nhập thì không cần vào nữa, chuyển về trang chính
const routes = [
  { path: '/', redirect: HOME_PATH },
  {
    path: '/products',
    name: 'products',
    component: ProductListPage,
    meta: { title: 'Sản phẩm' },
  },
  {
    path: '/categories',
    name: 'categories',
    component: CategoryListPage,
    meta: { title: 'Danh mục' },
  },
  {
    path: '/account',
    name: 'account',
    component: AccountPage,
    meta: { title: 'Tài khoản' },
  },
  {
    path: '/login',
    name: 'login',
    component: LoginPage,
    meta: { title: 'Đăng nhập', public: true, guestOnly: true },
  },
  {
    path: '/forgot-password',
    name: 'forgot-password',
    component: ForgotPasswordPage,
    meta: { title: 'Quên mật khẩu', public: true, guestOnly: true },
  },
  // Link trong mail đặt lại mật khẩu mà Flask gửi đi trỏ tới đúng đường dẫn này,
  // đổi đường dẫn ở đây thì link trong mail sẽ hỏng
  {
    path: '/reset-password',
    name: 'reset-password',
    component: ResetPasswordPage,
    meta: { title: 'Đặt lại mật khẩu', public: true },
  },
  // Gõ URL không có trong danh sách thì đưa về trang chính
  { path: '/:pathMatch(.*)*', redirect: HOME_PATH },
]

// createWebHistory: URL gọn kiểu /products (không có dấu #).
// Đổi lại server phải trả index.html cho mọi đường dẫn không phải /api,
// việc này nằm ở try_files trong docker/nginx/default.conf.
const router = createRouter({
  history: createWebHistory(),
  routes,
})

// beforeEach: chạy trước mỗi lần chuyển trang.
// Trả về true là cho đi tiếp, trả về một địa chỉ khác là chuyển hướng sang đó.
router.beforeEach((to) => {
  // Chưa đăng nhập mà vào trang không public: bắt đăng nhập trước
  if (!to.meta.public && !isLoggedIn()) {
    const loginLocation = { path: '/login' }

    // Gắn trang muốn vào vào ?redirect=, đăng nhập xong quay lại đúng trang đó.
    // Trang chính thì khỏi gắn, đăng nhập xong vốn đã về đó.
    if (to.fullPath !== HOME_PATH) {
      loginLocation.query = { redirect: to.fullPath }
    }
    return loginLocation
  }

  if (to.meta.guestOnly && isLoggedIn()) {
    return { path: HOME_PATH }
  }

  return true
})

// afterEach: chạy sau khi đã chuyển trang xong, đổi chữ trên tab trình duyệt
router.afterEach((to) => {
  if (to.meta.title) {
    document.title = `${to.meta.title} · ${APP_NAME}`
  } else {
    document.title = APP_NAME
  }
})

export default router
