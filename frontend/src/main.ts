import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'

// 创建应用实例，挂载 Pinia 状态管理与路由
const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')
