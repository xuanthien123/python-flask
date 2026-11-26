import { createRouter, createWebHistory } from 'vue-router'

import ProductListPage from '../pages/ProductListPage.vue'

// Mỗi dòng: URL nào thì hiện trang (component) nào.
// Thêm trang mới: tạo file trong src/pages rồi thêm một dòng ở đây.
const routes = [
  { path: '/', redirect: '/products' },
  { path: '/products', name: 'products', component: ProductListPage },
  // Gõ URL không có trong danh sách thì đưa về trang sản phẩm
  { path: '/:pathMatch(.*)*', redirect: '/products' },
]

// createWebHistory: URL gọn kiểu /products (không có dấu #).
// Đổi lại server phải trả index.html cho mọi đường dẫn không phải /api,
// việc này nằm ở try_files trong docker/nginx/default.conf.
const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
