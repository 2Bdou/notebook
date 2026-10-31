import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import { useAuthStore } from '@/stores/auth'

// 创建应用实例，挂载 Pinia 状态管理与路由
const app = createApp(App)
const pinia = createPinia()
app.use(pinia)
app.use(router)

// 从 localStorage 恢复登录态（必须在 router 挂载之前，否则守卫判断时还没有用户信息）
const authStore = useAuthStore()
authStore.initAuth()

app.mount('#app')
