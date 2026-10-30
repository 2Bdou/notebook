import { createRouter, createWebHistory } from 'vue-router'

// 路由配置：history 模式
const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/Home.vue')
    },
    {
      path: '/trash',
      name: 'trash',
      component: () => import('@/views/Trash.vue')
    }
  ]
})

export default router
