import { http } from './request'
import type { Note, NoteListResult, NoteForm } from '@/types'

// 笔记相关 API
export const noteApi = {
  /** 获取笔记列表（支持分类/标签/关键词过滤、排序与分页） */
  list(params: Record<string, any>): Promise<NoteListResult> {
    return http.get<NoteListResult>('/notes', { params })
  },

  /** 获取笔记详情 */
  detail(id: number): Promise<Note> {
    return http.get<Note>(`/notes/${id}`)
  },

  /** 新建笔记 */
  create(data: NoteForm): Promise<Note> {
    return http.post<Note>('/notes', data)
  },

  /** 更新笔记 */
  update(id: number, data: NoteForm): Promise<Note> {
    return http.put<Note>(`/notes/${id}`, data)
  },

  /** 软删除笔记 */
  remove(id: number): Promise<void> {
    return http.delete(`/notes/${id}`)
  },

  /** 恢复已软删除的笔记 */
  restore(id: number): Promise<void> {
    return http.post(`/notes/${id}/restore`)
  },

  /** 永久删除笔记（不可恢复） */
  forceDelete(id: number): Promise<void> {
    return http.delete(`/notes/${id}/force`)
  },

  /** 获取回收站笔记列表 */
  trashList(page = 1, pageSize = 50): Promise<NoteListResult> {
    return http.get<NoteListResult>('/notes/trash', {
      params: { page, page_size: pageSize }
    })
  },

  /** 批量恢复所有已删除笔记 */
  restoreAll(): Promise<{ restored_count: number }> {
    return http.post('/notes/restore-all')
  },

  /** 清空回收站 */
  emptyTrash(): Promise<{ deleted_count: number }> {
    return http.delete('/notes/empty-trash')
  },

  /** 全文搜索笔记（支持分类/标签二次过滤） */
  search(
    q: string,
    params?: { category_id?: number; tag_id?: number; page?: number; page_size?: number }
  ): Promise<NoteListResult> {
    return http.get<NoteListResult>('/search', {
      params: { q, ...params }
    })
  }
}
