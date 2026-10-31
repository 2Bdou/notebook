import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

// 路由配置：history 模式
const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/Login.vue'),
      meta: { public: true }
    },
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

// 全局前置守卫：未登录时重定向到登录页
router.beforeEach((to) => {
  const authStore = useAuthStore()

  // 非 public 路由需要登录
  if (!to.meta.public && !authStore.isAuthenticated) {
    return { name: 'login' }
  }

  // 已登录时访问登录页，重定向到首页
  if (to.name === 'login' && authStore.isAuthenticated) {
    return { name: 'home' }
  }
})

export default router
