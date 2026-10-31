import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { noteApi } from '@/api/note'
import type { Note, NoteForm, SortField, SortOrder } from '@/types'

// 笔记状态管理
export const useNoteStore = defineStore('note', () => {
  const notes = ref<Note[]>([])
  const total = ref(0)
  const current = ref<Note | null>(null)
  const loading = ref(false)
  const searching = ref(false) // 搜索专用 loading

  // 列表过滤条件
  const filter = ref({
    category_id: undefined as number | undefined,
    tag_id: undefined as number | undefined,
    q: '',
    sort: 'updated_at' as SortField,
    order: 'desc' as SortOrder,
    page: 1,
    page_size: 20
  })

  // 回收站笔记列表
  const trashNotes = ref<Note[]>([])
  const trashTotal = ref(0)
  const trashLoading = ref(false)

  /** 当前是否有过滤条件 */
  const hasFilter = computed(
    () =>
      filter.value.category_id !== undefined ||
      filter.value.tag_id !== undefined ||
      filter.value.q !== ''
  )

  /** 拉取笔记列表 */
  async function fetchNotes() {
    loading.value = true
    try {
      const params: Record<string, any> = { ...filter.value }
      // 清理空值参数
      Object.keys(params).forEach((k) => {
        if (params[k] === '' || params[k] === undefined || params[k] === null) {
          delete params[k]
        }
      })
      const res = await noteApi.list(params)
      notes.value = res.items
      total.value = res.total
    } finally {
      loading.value = false
    }
  }

  /** 获取笔记详情并设为当前编辑笔记 */
  async function fetchNote(id: number) {
    current.value = await noteApi.detail(id)
  }

  /** 新建笔记 */
  async function createNote(data: NoteForm) {
    return await noteApi.create(data)
  }

  /** 更新笔记 */
  async function updateNote(id: number, data: NoteForm) {
    return await noteApi.update(id, data)
  }

  /** 软删除笔记 */
  async function deleteNote(id: number) {
    await noteApi.remove(id)
  }

  /** 恢复笔记 */
  async function restoreNote(id: number) {
    await noteApi.restore(id)
  }

  /** 按分类过滤 */
  function setCategoryFilter(id?: number) {
    filter.value.category_id = id
    filter.value.page = 1
    fetchNotes()
  }

  /** 按标签过滤 */
  function setTagFilter(id?: number) {
    filter.value.tag_id = id
    filter.value.page = 1
    fetchNotes()
  }

  /** 关键词搜索（与分类/标签过滤组合使用，带 loading 状态） */
  function setSearch(q: string) {
    filter.value.q = q
    filter.value.page = 1
    searching.value = true
    fetchNotes().finally(() => {
      searching.value = false
    })
  }

  /** 设置排序字段 */
  function setSort(sort: SortField) {
    filter.value.sort = sort
    filter.value.page = 1
    fetchNotes()
  }

  /** 设置排序方向 */
  function setOrder(order: SortOrder) {
    filter.value.order = order
    filter.value.page = 1
    fetchNotes()
  }

  /** 清除所有过滤条件 */
  function clearFilters() {
    filter.value.category_id = undefined
    filter.value.tag_id = undefined
    filter.value.q = ''
    filter.value.page = 1
    fetchNotes()
  }

  /** 清除分类过滤 */
  function clearCategoryFilter() {
    filter.value.category_id = undefined
    filter.value.page = 1
    fetchNotes()
  }

  /** 清除标签过滤 */
  function clearTagFilter() {
    filter.value.tag_id = undefined
    filter.value.page = 1
    fetchNotes()
  }

  /** 更新笔记的标签关联（立即保存到后端） */
  async function updateNoteTags(id: number, tagIds: number[]) {
    return await noteApi.update(id, { tag_ids: tagIds })
  }

  // ==================== 回收站方法 ====================

  /** 获取回收站笔记列表 */
  async function fetchTrashNotes() {
    trashLoading.value = true
    try {
      const res = await noteApi.trashList()
      trashNotes.value = res.items
      trashTotal.value = res.total
    } finally {
      trashLoading.value = false
    }
  }

  /** 永久删除笔记 */
  async function forceDeleteNote(id: number) {
    await noteApi.forceDelete(id)
  }

  /** 批量恢复所有已删除笔记 */
  async function restoreAllNotes(): Promise<number> {
    const res = await noteApi.restoreAll()
    return res.restored_count
  }

  /** 清空回收站 */
  async function emptyTrash(): Promise<number> {
    const res = await noteApi.emptyTrash()
    return res.deleted_count
  }

  return {
    notes,
    total,
    current,
    loading,
    searching,
    filter,
    hasFilter,
    trashNotes,
    trashTotal,
    trashLoading,
    fetchNotes,
    fetchNote,
    createNote,
    updateNote,
    deleteNote,
    restoreNote,
    setCategoryFilter,
    setTagFilter,
    setSearch,
    setSort,
    setOrder,
    clearFilters,
    clearCategoryFilter,
    clearTagFilter,
    updateNoteTags,
    fetchTrashNotes,
    forceDeleteNote,
    restoreAllNotes,
    emptyTrash
  }
})
