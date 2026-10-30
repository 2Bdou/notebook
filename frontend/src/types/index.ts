/** 后端统一响应格式 */
export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
}

/** 笔记关联的标签简要信息 */
export interface NoteTag {
  id: number
  name: string
}

/** 笔记 */
export interface Note {
  id: number
  title: string
  content: string
  content_html: string
  category_id: number | null
  is_pinned: boolean
  word_count: number
  created_at: string
  updated_at: string
  deleted_at: string | null
  tags: NoteTag[]
  /** 搜索结果：匹配类型（title/content/both） */
  match_type?: string
  /** 搜索结果：匹配摘要片段 */
  snippet?: string
}

/** 笔记列表分页结果 */
export interface NoteListResult {
  total: number
  page: number
  page_size: number
  items: Note[]
}

/** 分类（支持树形 children） */
export interface Category {
  id: number
  name: string
  parent_id: number | null
  sort_order: number
  created_at: string
  children?: Category[]
}

/** 标签（含关联笔记数） */
export interface Tag {
  id: number
  name: string
  created_at: string
  note_count: number
}

/** 新建/更新笔记的表单参数 */
export interface NoteForm {
  title?: string
  content?: string
  content_html?: string
  category_id?: number | null
  is_pinned?: boolean
  tag_ids?: number[]
}

/** 排序方式 */
export type SortField = 'updated_at' | 'created_at' | 'title' | 'word_count'
/** 排序方向 */
export type SortOrder = 'desc' | 'asc'
