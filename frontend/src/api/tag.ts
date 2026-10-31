import { http } from './request'
import type { Tag } from '@/types'

// 标签相关 API
export const tagApi = {
  /** 获取所有标签（含笔记计数） */
  list(): Promise<Tag[]> {
    return http.get<Tag[]>('/tags')
  },

  /** 新建标签 */
  create(name: string): Promise<Tag> {
    return http.post<Tag>('/tags', { name })
  },

  /** 删除标签 */
  remove(id: number): Promise<void> {
    return http.delete(`/tags/${id}`)
  }
}
