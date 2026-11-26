import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  // Plugin này giúp Vite hiểu file .vue
  plugins: [vue()],

  server: {
    port: 5173,
    // Lúc dev, trang chạy ở localhost:5173 còn API ở nginx localhost:8080.
    // Khác cổng là khác địa chỉ, trình duyệt sẽ chặn vì Flask chưa bật CORS.
    // Proxy: trình duyệt gọi /api/... ở 5173, Vite tự chuyển sang 8080 giùm.
    proxy: {
      '/api': 'http://localhost:8080',
    },
  },
})
