import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { categoryApi } from '@/api/category'
import type { Category } from '@/types'

// 分类状态管理
export const useCategoryStore = defineStore('category', () => {
  const categories = ref<Category[]>([])
  const loading = ref(false)
  const selectedCategoryId = ref<number | undefined>(undefined) // 当前选中的分类 ID
  const error = ref<string>('') // 错误信息

  /** 拉取全部分类 */
  async function fetchCategories() {
    loading.value = true
    error.value = ''
    try {
      categories.value = await categoryApi.list()
    } catch (err: any) {
      error.value = err?.message || '加载分类失败'
    } finally {
      loading.value = false
    }
  }

  /** 新建分类并刷新列表 */
  async function createCategory(data: { name: string; parent_id?: number | null }) {
    error.value = ''
    try {
      const cat = await categoryApi.create(data)
      await fetchCategories()
      return cat
    } catch (err: any) {
      error.value = err?.message || '创建分类失败'
      throw err
    }
  }

  /** 更新分类并刷新列表 */
  async function updateCategory(
    id: number,
    data: Partial<{ name: string; parent_id: number | null; sort_order: number }>
  ) {
    error.value = ''
    try {
      const cat = await categoryApi.update(id, data)
      await fetchCategories()
      return cat
    } catch (err: any) {
      error.value = err?.message || '更新分类失败'
      throw err
    }
  }

  /** 删除分类并刷新列表 */
  async function deleteCategory(id: number) {
    error.value = ''
    try {
      await categoryApi.remove(id)
      // 如果删除的是当前选中的分类，清除选中
      if (selectedCategoryId.value === id) {
        selectedCategoryId.value = undefined
      }
      await fetchCategories()
    } catch (err: any) {
      error.value = err?.message || '删除分类失败'
      throw err
    }
  }

  /** 选中分类（再次点击同一分类则取消） */
  function selectCategory(id: number | undefined) {
    selectedCategoryId.value =
      selectedCategoryId.value === id ? undefined : id
  }

  /** 将平铺列表构建为树形结构 */
  const categoryTree = computed<Category[]>(() => {
    const map = new Map<number, Category>()
    categories.value.forEach((c) => map.set(c.id, { ...c, children: [] }))
    const roots: Category[] = []
    map.forEach((c) => {
      if (c.parent_id && map.has(c.parent_id)) {
        map.get(c.parent_id)!.children!.push(c)
      } else {
        roots.push(c)
      }
    })
    return roots
  })

  /** 根据 ID 获取分类名称 */
  function getCategoryName(id: number | undefined): string {
    if (!id) return ''
    const cat = categories.value.find((c) => c.id === id)
    return cat?.name || ''
  }

  /** 根据 ID 获取分类对象 */
  function getCategoryById(id: number | undefined): Category | undefined {
    if (!id) return undefined
    return categories.value.find((c) => c.id === id)
  }

  /** 获取指定分类下（含子分类）的笔记数 — 前端无此数据时返回 0 */
  function getNoteCount(_id: number): number {
    return 0
  }

  return {
    categories,
    categoryTree,
    loading,
    selectedCategoryId,
    error,
    fetchCategories,
    createCategory,
    updateCategory,
    deleteCategory,
    selectCategory,
    getCategoryName,
    getCategoryById,
    getNoteCount
  }
})
