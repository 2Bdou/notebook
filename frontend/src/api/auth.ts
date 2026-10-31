import { http } from './request'
import type { AuthResult, User } from '@/types'

export const authApi = {
  /** 用户注册 */
  register(username: string, password: string): Promise<AuthResult> {
    return http.post('/auth/register', { username, password })
  },

  /** 用户登录 */
  login(username: string, password: string): Promise<AuthResult> {
    return http.post('/auth/login', { username, password })
  },

  /** 获取当前用户信息 */
  me(): Promise<User> {
    return http.get('/auth/me')
  }
}
