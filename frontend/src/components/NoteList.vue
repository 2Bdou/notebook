<template>
  <div class="note-list">
    <!-- 搜索框 -->
    <div class="search-bar">
      <input
        v-model="keyword"
        class="search-input"
        placeholder="搜索笔记...（至少 2 个字符）"
        @input="onSearch"
      />
      <!-- 搜索 loading 指示器 -->
      <span v-if="noteStore.searching" class="search-loading">⏳</span>
    </div>

    <!-- 排序工具栏 -->
    <div class="sort-bar">
      <select class="sort-select" :value="noteStore.filter.sort" @change="onSortChange">
        <option value="updated_at">更新时间</option>
        <option value="created_at">创建时间</option>
        <option value="title">标题</option>
        <option value="word_count">字数</option>
      </select>
      <button class="sort-order-btn" :title="noteStore.filter.order === 'desc' ? '降序' : '升序'" @click="toggleOrder">
        {{ noteStore.filter.order === 'desc' ? '↓' : '↑' }}
      </button>
    </div>

    <!-- 当前过滤条件展示 -->
    <div v-if="noteStore.hasFilter" class="filter-bar">
      <!-- 分类过滤标签 -->
      <span v-if="noteStore.filter.category_id" class="filter-chip">
        分类: {{ categoryStore.getCategoryName(noteStore.filter.category_id) }}
        <button class="chip-close" @click="noteStore.clearCategoryFilter()">✕</button>
      </span>
      <!-- 标签过滤标签 -->
      <span v-if="noteStore.filter.tag_id" class="filter-chip">
        标签: {{ tagStore.getTagName(noteStore.filter.tag_id) }}
        <button class="chip-close" @click="noteStore.clearTagFilter()">✕</button>
      </span>
      <!-- 搜索关键词标签 -->
      <span v-if="noteStore.filter.q" class="filter-chip">
        搜索: {{ noteStore.filter.q }}
        <button class="chip-close" @click="clearSearch">✕</button>
      </span>
      <!-- 清除全部过滤 -->
      <button class="btn-clear-all" @click="clearAllFilters">清除全部</button>
    </div>

    <!-- 笔记卡片列表 -->
    <div class="list-body">
      <!-- 列表 loading -->
      <div v-if="noteStore.loading && !noteStore.notes.length" class="list-loading">
        加载中...
      </div>

      <template v-else>
        <!-- 置顶笔记区 -->
        <template v-for="note in noteStore.notes" :key="note.id">
          <!-- 置顶与普通笔记之间的分隔线 -->
          <div
            v-if="showPinSeparator(note)"
            class="pin-separator"
          >
            <span class="separator-text">普通笔记</span>
          </div>

          <div
            class="note-card"
            :class="{ active: noteStore.current?.id === note.id }"
            @click="selectNote(note)"
            @contextmenu.prevent="onContextMenu($event, note)"
          >
            <div class="note-title">
              <span v-if="note.is_pinned" class="pin-icon" title="已置顶">📌</span>
              <span class="title-text" v-html="highlightTitle(note.title)"></span>
            </div>
            <div class="note-summary" v-html="highlightSummary(note)"></div>
            <div class="note-meta">
              <span class="update-time">{{ formatDate(note.updated_at) }}</span>
              <span class="note-tags">
                <span v-for="t in note.tags" :key="t.id" class="mini-tag">{{ t.name }}</span>
              </span>
            </div>
          </div>
        </template>

        <!-- 空状态 -->
        <div v-if="!noteStore.notes.length && !noteStore.loading" class="empty-state">
          <template v-if="noteStore.filter.q">
            未找到相关笔记
          </template>
          <template v-else>
            {{ noteStore.hasFilter ? '没有符合条件的笔记' : '暂无笔记，点击左侧「新建笔记」开始记录' }}
          </template>
        </div>
      </template>
    </div>

    <!-- 右键菜单 -->
    <div
      v-if="contextMenu.visible"
      class="context-menu"
      :style="{ top: contextMenu.y + 'px', left: contextMenu.x + 'px' }"
      @click.stop
    >
      <button class="ctx-item" @click="quickTogglePin">
        {{ contextMenu.note?.is_pinned ? '取消置顶' : '📌 置顶' }}
      </button>
      <button class="ctx-item ctx-danger" @click="quickDelete">🗑 删除</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useNoteStore } from '@/stores/note'
import { useCategoryStore } from '@/stores/category'
import { useTagStore } from '@/stores/tag'
import type { Note, SortField, SortOrder } from '@/types'

const noteStore = useNoteStore()
const categoryStore = useCategoryStore()
const tagStore = useTagStore()
const keyword = ref('')

// ==================== 搜索防抖（300ms） ====================
let searchTimer: ReturnType<typeof setTimeout> | null = null
function onSearch() {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    noteStore.setSearch(keyword.value)
  }, 300)
}

/** 清除搜索关键词 */
function clearSearch() {
  keyword.value = ''
  noteStore.setSearch('')
}

/** 清除所有过滤条件 */
function clearAllFilters() {
  keyword.value = ''
  noteStore.clearFilters()
}

// ==================== 排序功能 ====================
/** 排序字段变更 */
function onSortChange(e: Event) {
  const value = (e.target as HTMLSelectElement).value as SortField
  noteStore.setSort(value)
  // 持久化到 localStorage
  saveSortState()
}

/** 切换排序方向 */
function toggleOrder() {
  const newOrder: SortOrder = noteStore.filter.order === 'desc' ? 'asc' : 'desc'
  noteStore.setOrder(newOrder)
  saveSortState()
}

/** 保存排序状态到 localStorage */
function saveSortState() {
  localStorage.setItem('note_sort', noteStore.filter.sort)
  localStorage.setItem('note_order', noteStore.filter.order)
}

/** 从 localStorage 恢复排序状态 */
function restoreSortState() {
  const savedSort = localStorage.getItem('note_sort') as SortField | null
  const savedOrder = localStorage.getItem('note_order') as SortOrder | null
  if (savedSort) noteStore.filter.sort = savedSort
  if (savedOrder) noteStore.filter.order = savedOrder
}

// ==================== 选中笔记 ====================
function selectNote(note: Note) {
  noteStore.fetchNote(note.id)
}

// ==================== 搜索高亮 ====================
/** 转义 HTML 特殊字符 */
function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
  }

/** 高亮标题中的搜索关键词 */
function highlightTitle(title: string): string {
  const q = noteStore.filter.q
  if (!q || q.length < 2) return escapeHtml(title || '无标题')
  return highlightKeyword(title || '无标题', q)
}

/** 高亮摘要中的搜索关键词 */
function highlightSummary(note: Note): string {
  const q = noteStore.filter.q
  const text = getSummary(note.content)
  if (!q || q.length < 2) return escapeHtml(text)
  return highlightKeyword(text, q)
}

/** 在文本中高亮关键词（用 <mark> 标签包裹） */
function highlightKeyword(text: string, keyword: string): string {
  const escaped = escapeHtml(text)
  const escKeyword = escapeHtml(keyword)
  // 大小写不敏感替换
  const regex = new RegExp(`(${escKeyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi')
  return escaped.replace(regex, '<mark class="search-highlight">$1</mark>')
}

// ==================== 置顶分隔线 ====================
/** 判断是否在当前笔记前显示置顶/普通分隔线 */
function showPinSeparator(note: Note): boolean {
  const notes = noteStore.notes
  const idx = notes.findIndex((n) => n.id === note.id)
  if (idx <= 0) return false
  // 前一条是置顶，当前不是 → 分隔线
  return notes[idx - 1].is_pinned && !note.is_pinned
}

// ==================== 右键菜单 ====================
const contextMenu = ref({
  visible: false,
  x: 0,
  y: 0,
  note: null as Note | null
})

/** 打开右键菜单 */
function onContextMenu(e: MouseEvent, note: Note) {
  contextMenu.value = {
    visible: true,
    x: e.clientX,
    y: e.clientY,
    note
  }
}

/** 关闭右键菜单 */
function closeContextMenu() {
  contextMenu.value.visible = false
}

/** 右键菜单：快速置顶/取消置顶 */
async function quickTogglePin() {
  const note = contextMenu.value.note
  if (!note) return
  closeContextMenu()
  try {
    const pinned = !note.is_pinned
    await noteStore.updateNote(note.id, { is_pinned: pinned })
    // 更新列表中对应笔记的置顶状态
    const target = noteStore.notes.find((n) => n.id === note.id)
    if (target) target.is_pinned = pinned
    // 如果是当前编辑的笔记也同步
    if (noteStore.current?.id === note.id) {
      noteStore.current.is_pinned = pinned
    }
    // 重新加载列表以应用排序（置顶笔记移到最前）
    await noteStore.fetchNotes()
  } catch (err: any) {
    alert(err?.message || '操作失败')
  }
}

/** 右键菜单：快速删除 */
async function quickDelete() {
  const note = contextMenu.value.note
  if (!note) return
  closeContextMenu()
  if (!confirm(`确定删除「${note.title || '无标题'}」？`)) return
  try {
    await noteStore.deleteNote(note.id)
    // 如果删除的是当前编辑的笔记，清空编辑区
    if (noteStore.current?.id === note.id) {
      noteStore.current = null
    }
    await noteStore.fetchNotes()
  } catch (err: any) {
    alert(err?.message || '删除失败')
  }
}

// ==================== 工具函数 ====================
/** 提取内容摘要（去除 Markdown 符号后取前 80 字） */
function getSummary(content: string): string {
  const text = content.replace(/[#*`>\-\[\]()!]/g, '').trim()
  return text.slice(0, 80) || '无内容'
}

/** 格式化日期为相对时间 */
function formatDate(dateStr: string): string {
  const d = new Date(dateStr.replace(' ', 'T'))
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return Math.floor(diff / 60000) + '分钟前'
  if (diff < 86400000) return Math.floor(diff / 3600000) + '小时前'
  return `${d.getMonth() + 1}月${d.getDate()}日`
}

// ==================== 侦听器 ====================
// 当过滤条件中的搜索词被外部清除时，同步本地 keyword
watch(
  () => noteStore.filter.q,
  (q) => {
    if (!q && keyword.value) keyword.value = ''
  }
)

// ==================== 生命周期 ====================
onMounted(() => {
  restoreSortState()
  document.addEventListener('click', closeContextMenu)
})

onUnmounted(() => {
  document.removeEventListener('click', closeContextMenu)
})
</script>

<style scoped>
.note-list {
  width: 320px;
  flex-shrink: 0;
  background: #fff;
  border-right: 1px solid #e0e0e0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
/* 搜索框 */
.search-bar {
  position: relative;
  padding: 12px;
  border-bottom: 1px solid #eee;
}
.search-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  box-sizing: border-box;
}
.search-input:focus {
  border-color: #42b983;
  outline: none;
}
.search-loading {
  position: absolute;
  right: 20px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 14px;
  animation: spin 1s linear infinite;
}
@keyframes spin {
  from { transform: translateY(-50%) rotate(0deg); }
  to { transform: translateY(-50%) rotate(360deg); }
}
/* 排序工具栏 */
.sort-bar {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-bottom: 1px solid #eee;
  background: #fafafa;
}
.sort-select {
  flex: 1;
  padding: 4px 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 12px;
  background: #fff;
  cursor: pointer;
  outline: none;
}
.sort-select:focus {
  border-color: #42b983;
}
.sort-order-btn {
  padding: 4px 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: #fff;
  cursor: pointer;
  font-size: 14px;
  line-height: 1;
}
.sort-order-btn:hover {
  border-color: #42b983;
  color: #42b983;
}
/* 过滤条件标签栏 */
.filter-bar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
  padding: 8px 12px;
  border-bottom: 1px solid #eee;
  background: #f9fbf9;
}
.filter-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  background: #e8f5e9;
  color: #42b983;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}
.chip-close {
  border: none;
  background: none;
  cursor: pointer;
  font-size: 10px;
  color: #42b983;
  padding: 0;
  line-height: 1;
  opacity: 0.6;
}
.chip-close:hover {
  opacity: 1;
}
.btn-clear-all {
  border: none;
  background: none;
  cursor: pointer;
  font-size: 12px;
  color: #f56c6c;
  padding: 3px 4px;
  margin-left: auto;
}
.btn-clear-all:hover {
  text-decoration: underline;
}
/* 笔记列表 */
.list-body {
  flex: 1;
  overflow-y: auto;
  position: relative;
}
.list-loading {
  text-align: center;
  color: #999;
  padding: 40px 16px;
  font-size: 14px;
}
/* 置顶分隔线 */
.pin-separator {
  display: flex;
  align-items: center;
  padding: 6px 16px;
  background: #f5f5f5;
  border-top: 1px solid #e0e0e0;
  border-bottom: 1px solid #e0e0e0;
}
.separator-text {
  font-size: 11px;
  color: #aaa;
  letter-spacing: 1px;
}
.note-card {
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
}
.note-card:hover {
  background: #f9f9f9;
}
.note-card.active {
  background: #e8f5e9;
  border-left: 3px solid #42b983;
}
.note-title {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 15px;
  font-weight: 500;
  margin-bottom: 4px;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
.pin-icon {
  flex-shrink: 0;
  font-size: 13px;
}
.title-text {
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
.note-summary {
  font-size: 13px;
  color: #888;
  margin-bottom: 6px;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
.note-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.update-time {
  font-size: 12px;
  color: #aaa;
}
.note-tags {
  display: flex;
  gap: 4px;
}
.mini-tag {
  font-size: 11px;
  color: #42b983;
  background: #e8f5e9;
  padding: 1px 6px;
  border-radius: 8px;
}
.empty-state {
  text-align: center;
  color: #999;
  padding: 40px 16px;
  font-size: 14px;
}
/* 右键菜单 */
.context-menu {
  position: fixed;
  z-index: 1000;
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 6px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  overflow: hidden;
  min-width: 120px;
}
.ctx-item {
  display: block;
  width: 100%;
  padding: 8px 16px;
  border: none;
  background: none;
  cursor: pointer;
  font-size: 13px;
  text-align: left;
}
.ctx-item:hover {
  background: #f0f7f4;
}
.ctx-danger:hover {
  background: #fef0f0;
  color: #f56c6c;
}
/* 搜索高亮（全局样式，因为 v-html 生成的 DOM 不受 scoped 限制） */
:deep(.search-highlight) {
  background: #fff3cd;
  color: #e6a23c;
  padding: 0 2px;
  border-radius: 2px;
  font-weight: 600;
}
</style>
