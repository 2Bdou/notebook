import { defineStore } from 'pinia'
import { ref } from 'vue'
import { tagApi } from '@/api/tag'
import type { Tag } from '@/types'

// 标签状态管理
export const useTagStore = defineStore('tag', () => {
  const tags = ref<Tag[]>([])
  const loading = ref(false)
  const selectedTagId = ref<number | undefined>(undefined) // 当前选中的标签 ID
  const error = ref<string>('') // 错误信息

  /** 拉取全部标签 */
  async function fetchTags() {
    loading.value = true
    error.value = ''
    try {
      tags.value = await tagApi.list()
    } catch (err: any) {
      error.value = err?.message || '加载标签失败'
    } finally {
      loading.value = false
    }
  }

  /** 新建标签并刷新列表 */
  async function createTag(name: string) {
    error.value = ''
    try {
      const tag = await tagApi.create(name)
      await fetchTags()
      return tag
    } catch (err: any) {
      error.value = err?.message || '创建标签失败'
      throw err
    }
  }

  /** 删除标签并刷新列表 */
  async function deleteTag(id: number) {
    error.value = ''
    try {
      await tagApi.remove(id)
      // 如果删除的是当前选中的标签，清除选中
      if (selectedTagId.value === id) {
        selectedTagId.value = undefined
      }
      await fetchTags()
    } catch (err: any) {
      error.value = err?.message || '删除标签失败'
      throw err
    }
  }

  /** 选中标签（再次点击同一标签则取消） */
  function selectTag(id: number | undefined) {
    selectedTagId.value = selectedTagId.value === id ? undefined : id
  }

  /** 根据名称查找标签（用于检查重名） */
  function findByName(name: string): Tag | undefined {
    return tags.value.find((t) => t.name === name)
  }

  /** 根据 ID 获取标签对象 */
  function getTagById(id: number | undefined): Tag | undefined {
    if (!id) return undefined
    return tags.value.find((t) => t.id === id)
  }

  /** 根据 ID 获取标签名称 */
  function getTagName(id: number | undefined): string {
    if (!id) return ''
    return tags.value.find((t) => t.id === id)?.name || ''
  }

  return {
    tags,
    loading,
    selectedTagId,
    error,
    fetchTags,
    createTag,
    deleteTag,
    selectTag,
    findByName,
    getTagById,
    getTagName
  }
})
