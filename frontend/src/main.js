import { createApp } from 'vue'

import App from './App.vue'
import router from './router/index.js'
import './style.css'

const app = createApp(App)

// Gắn router vào app để dùng được <RouterView> và <RouterLink>
app.use(router)

// Vẽ app vào <div id="app"> trong index.html
app.mount('#app')
