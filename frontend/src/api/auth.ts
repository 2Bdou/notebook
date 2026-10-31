import { http } from './request'
import type { AuthResult, User } from '@/types'

export const authApi = {
  /** 用户注册 */
  register(username: string, password: string, registration_code?: string): Promise<AuthResult> {
    return http.post('/auth/register', { username, password, registration_code: registration_code || '' })
  },

  /** 用户登录 */
  login(username: string, password: string): Promise<AuthResult> {
    return http.post('/auth/login', { username, password })
  },

  /** 获取当前用户信息 */
  me(): Promise<User> {
    return http.get('/auth/me')
  },

  /** 获取认证配置（是否允许注册、是否需要邀请码） */
  config(): Promise<{ allow_registration: boolean; need_registration_code: boolean }> {
    return http.get('/auth/config')
  }
}
