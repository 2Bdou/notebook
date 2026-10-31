import axios from 'axios'
import type { ApiResponse } from '@/types'

// 创建 axios 实例，baseURL 指向后端 /api
const instance = axios.create({
  baseURL: '/api',
  timeout: 10000
})

// 请求拦截器：自动附加 JWT token
instance.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器：统一提取 data 字段并处理错误
instance.interceptors.response.use(
  (response) => {
    const res = response.data as ApiResponse
    if (res.code !== 0) {
      console.error('[API Error]', res.message)
      return Promise.reject(new Error(res.message))
    }
    // 直接返回业务数据，剥离外层包装
    return res.data
  },
  (error) => {
    // 401 表示 token 失效或未登录，清除登录态并跳转登录页
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    console.error('[Request Error]', error.message)
    return Promise.reject(error)
  }
)

// 封装常用请求方法，泛型 T 表示返回的业务数据类型
export const http = {
  get<T = any>(url: string, config?: any): Promise<T> {
    return instance.get(url, config) as unknown as Promise<T>
  },
  post<T = any>(url: string, data?: any, config?: any): Promise<T> {
    return instance.post(url, data, config) as unknown as Promise<T>
  },
  put<T = any>(url: string, data?: any, config?: any): Promise<T> {
    return instance.put(url, data, config) as unknown as Promise<T>
  },
  delete<T = any>(url: string, config?: any): Promise<T> {
    return instance.delete(url, config) as unknown as Promise<T>
  }
}

export default instance
