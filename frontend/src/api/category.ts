import { http } from './request'
import type { Category } from '@/types'

// 分类相关 API
export const categoryApi = {
  /** 获取分类列表 */
  list(): Promise<Category[]> {
    return http.get<Category[]>('/categories')
  },

  /** 新建分类 */
  create(data: {
    name: string
    parent_id?: number | null
    sort_order?: number
  }): Promise<Category> {
    return http.post<Category>('/categories', data)
  },

  /** 更新分类（重命名 / 移动父级 / 排序） */
  update(
    id: number,
    data: Partial<{ name: string; parent_id: number | null; sort_order: number }>
  ): Promise<Category> {
    return http.put<Category>(`/categories/${id}`, data)
  },

  /** 删除分类 */
  remove(id: number): Promise<void> {
    return http.delete(`/categories/${id}`)
  }
}
