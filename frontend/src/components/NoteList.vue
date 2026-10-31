<template>
  <div class="note-list">
    <!-- 搜索框 -->
    <div class="search-bar">
      <Icon name="search" :size="16" class="search-icon" />
      <input
        v-model="keyword"
        class="search-input"
        placeholder="搜索笔记...（至少 2 个字符）"
        aria-label="搜索笔记"
        @input="onSearch"
      />
      <Icon v-if="noteStore.searching" name="loader" :size="16" class="search-loading spin" />
    </div>

    <!-- 排序工具栏 -->
    <div class="sort-bar">
      <select class="sort-select" aria-label="排序方式" :value="noteStore.filter.sort" @change="onSortChange">
        <option value="updated_at">更新时间</option>
        <option value="created_at">创建时间</option>
        <option value="title">标题</option>
        <option value="word_count">字数</option>
      </select>
      <button
        class="sort-order-btn"
        :aria-label="noteStore.filter.order === 'desc' ? '降序排列' : '升序排列'"
        @click="toggleOrder"
      >
        <Icon :name="noteStore.filter.order === 'desc' ? 'arrow-down' : 'arrow-up'" :size="14" />
      </button>
    </div>

    <!-- 当前过滤条件展示 -->
    <div v-if="noteStore.hasFilter" class="filter-bar">
      <span v-if="noteStore.filter.category_id" class="filter-chip">
        分类: {{ categoryStore.getCategoryName(noteStore.filter.category_id) }}
        <button class="chip-close" aria-label="清除分类过滤" @click="noteStore.clearCategoryFilter()">
          <Icon name="x" :size="10" />
        </button>
      </span>
      <span v-if="noteStore.filter.tag_id" class="filter-chip">
        标签: {{ tagStore.getTagName(noteStore.filter.tag_id) }}
        <button class="chip-close" aria-label="清除标签过滤" @click="noteStore.clearTagFilter()">
          <Icon name="x" :size="10" />
        </button>
      </span>
      <span v-if="noteStore.filter.q" class="filter-chip">
        搜索: {{ noteStore.filter.q }}
        <button class="chip-close" aria-label="清除搜索" @click="clearSearch">
          <Icon name="x" :size="10" />
        </button>
      </span>
      <button class="btn-clear-all" @click="clearAllFilters">清除全部</button>
    </div>

    <!-- 笔记卡片列表 -->
    <div class="list-body">
      <div v-if="noteStore.loading && !noteStore.notes.length" class="list-loading">
        加载中...
      </div>

      <template v-else>
        <template v-for="note in noteStore.notes" :key="note.id">
          <div v-if="showPinSeparator(note)" class="pin-separator">
            <span class="separator-text">普通笔记</span>
          </div>

          <div
            class="note-card"
            :class="{ active: noteStore.current?.id === note.id }"
            @click="selectNote(note)"
            @contextmenu.prevent="onContextMenu($event, note)"
          >
            <div class="note-title">
              <Icon v-if="note.is_pinned" name="pin" :size="14" class="pin-icon" />
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

        <div v-if="!noteStore.notes.length && !noteStore.loading" class="empty-state">
          <template v-if="noteStore.filter.q">未找到相关笔记</template>
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
        <Icon name="pin" :size="14" />
        <span>{{ contextMenu.note?.is_pinned ? '取消置顶' : '置顶' }}</span>
      </button>
      <button class="ctx-item ctx-danger" @click="quickDelete">
        <Icon name="trash" :size="14" />
        <span>删除</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import Icon from '@/components/Icon.vue'
import { useNoteStore } from '@/stores/note'
import { useCategoryStore } from '@/stores/category'
import { useTagStore } from '@/stores/tag'
import type { Note, SortField, SortOrder } from '@/types'

const noteStore = useNoteStore()
const categoryStore = useCategoryStore()
const tagStore = useTagStore()
const keyword = ref('')

let searchTimer: ReturnType<typeof setTimeout> | null = null
function onSearch() {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => { noteStore.setSearch(keyword.value) }, 300)
}
function clearSearch() { keyword.value = ''; noteStore.setSearch('') }
function clearAllFilters() { keyword.value = ''; noteStore.clearFilters() }
function onSortChange(e: Event) {
  noteStore.setSort((e.target as HTMLSelectElement).value as SortField); saveSortState()
}
function toggleOrder() {
  noteStore.setOrder(noteStore.filter.order === 'desc' ? 'asc' : 'desc'); saveSortState()
}
function saveSortState() {
  localStorage.setItem('note_sort', noteStore.filter.sort)
  localStorage.setItem('note_order', noteStore.filter.order)
}
function restoreSortState() {
  const s = localStorage.getItem('note_sort') as SortField | null
  const o = localStorage.getItem('note_order') as SortOrder | null
  if (s) noteStore.filter.sort = s
  if (o) noteStore.filter.order = o
}
function selectNote(note: Note) { noteStore.fetchNote(note.id) }
function escapeHtml(t: string): string {
  return t.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
}
function highlightTitle(title: string): string {
  const q = noteStore.filter.q
  if (!q || q.length < 2) return escapeHtml(title || '无标题')
  return highlightKeyword(title || '无标题', q)
}
function highlightSummary(note: Note): string {
  const q = noteStore.filter.q
  const text = getSummary(note.content)
  if (!q || q.length < 2) return escapeHtml(text)
  return highlightKeyword(text, q)
}
function highlightKeyword(text: string, kw: string): string {
  const escaped = escapeHtml(text)
  const escKw = escapeHtml(kw)
  const regex = new RegExp(`(${escKw.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi')
  return escaped.replace(regex, '<mark class="search-highlight">$1</mark>')
}
function showPinSeparator(note: Note): boolean {
  const notes = noteStore.notes
  const idx = notes.findIndex((n) => n.id === note.id)
  if (idx <= 0) return false
  return notes[idx - 1].is_pinned && !note.is_pinned
}
const contextMenu = ref({ visible: false, x: 0, y: 0, note: null as Note | null })
function onContextMenu(e: MouseEvent, note: Note) {
  contextMenu.value = { visible: true, x: e.clientX, y: e.clientY, note }
}
function closeContextMenu() { contextMenu.value.visible = false }
async function quickTogglePin() {
  const note = contextMenu.value.note; if (!note) return; closeContextMenu()
  try {
    const pinned = !note.is_pinned
    await noteStore.updateNote(note.id, { is_pinned: pinned })
    const target = noteStore.notes.find((n) => n.id === note.id)
    if (target) target.is_pinned = pinned
    if (noteStore.current?.id === note.id) noteStore.current.is_pinned = pinned
    await noteStore.fetchNotes()
  } catch (err: any) { alert(err?.message || '操作失败') }
}
async function quickDelete() {
  const note = contextMenu.value.note; if (!note) return; closeContextMenu()
  if (!confirm(`确定删除「${note.title || '无标题'}」？`)) return
  try {
    await noteStore.deleteNote(note.id)
    if (noteStore.current?.id === note.id) noteStore.current = null
    await noteStore.fetchNotes()
  } catch (err: any) { alert(err?.message || '删除失败') }
}
function getSummary(content: string): string {
  return content.replace(/[#*`>\-\[\]()!]/g, '').trim().slice(0, 80) || '无内容'
}
function formatDate(dateStr: string): string {
  const d = new Date(dateStr.replace(' ', 'T'))
  const diff = Date.now() - d.getTime()
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return Math.floor(diff / 60000) + '分钟前'
  if (diff < 86400000) return Math.floor(diff / 3600000) + '小时前'
  return `${d.getMonth() + 1}月${d.getDate()}日`
}
watch(() => noteStore.filter.q, (q) => { if (!q && keyword.value) keyword.value = '' })
onMounted(() => { restoreSortState(); document.addEventListener('click', closeContextMenu) })
onUnmounted(() => { document.removeEventListener('click', closeContextMenu) })
</script>

<style scoped>
.note-list { width: 320px; flex-shrink: 0; background: var(--color-bg-card); border-right: 1px solid var(--color-border); display: flex; flex-direction: column; overflow: hidden; }
.search-bar { position: relative; padding: var(--space-3); border-bottom: 1px solid var(--color-border-light); display: flex; align-items: center; gap: var(--space-2); }
.search-icon { color: var(--color-text-tertiary); flex-shrink: 0; }
.search-input { flex: 1; padding: 8px 0; border: none; font-size: 14px; background: transparent; color: var(--color-text-primary); }
.search-input::placeholder { color: var(--color-text-tertiary); }
.search-loading { color: var(--color-text-tertiary); flex-shrink: 0; }
.sort-bar { display: flex; align-items: center; gap: 6px; padding: 6px var(--space-3); border-bottom: 1px solid var(--color-border-light); background: var(--color-bg); }
.sort-select { flex: 1; padding: 6px 8px; border: 1px solid var(--color-border); border-radius: var(--radius-md); font-size: 12px; background: var(--color-bg-card); color: var(--color-text-primary); cursor: pointer; min-height: 32px; }
.sort-select:focus { border-color: var(--color-primary); }
.sort-order-btn { padding: 6px 10px; border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-bg-card); cursor: pointer; display: flex; align-items: center; justify-content: center; color: var(--color-text-secondary); min-height: 32px; min-width: 32px; transition: all var(--transition-fast); }
.sort-order-btn:hover { border-color: var(--color-primary); color: var(--color-primary); }
.filter-bar { display: flex; align-items: center; flex-wrap: wrap; gap: 6px; padding: 8px var(--space-3); border-bottom: 1px solid var(--color-border-light); background: var(--color-primary-bg); }
.filter-chip { display: inline-flex; align-items: center; gap: 4px; padding: 4px 8px; background: var(--color-primary-light); color: var(--color-primary-hover); border-radius: var(--radius-full); font-size: 12px; font-weight: 500; }
.chip-close { cursor: pointer; color: var(--color-primary-hover); padding: 2px; display: flex; align-items: center; line-height: 1; opacity: 0.6; transition: opacity var(--transition-fast); }
.chip-close:hover { opacity: 1; }
.btn-clear-all { cursor: pointer; font-size: 12px; color: var(--color-danger); padding: 4px; margin-left: auto; }
.btn-clear-all:hover { text-decoration: underline; }
.list-body { flex: 1; overflow-y: auto; position: relative; }
.list-loading { text-align: center; color: var(--color-text-tertiary); padding: 40px var(--space-4); font-size: 14px; }
.pin-separator { display: flex; align-items: center; padding: 6px var(--space-4); background: var(--color-bg); border-top: 1px solid var(--color-border); border-bottom: 1px solid var(--color-border); }
.separator-text { font-size: 11px; color: var(--color-text-tertiary); letter-spacing: 1px; font-weight: 500; }
.note-card { padding: var(--space-3) var(--space-4); border-bottom: 1px solid var(--color-border-light); cursor: pointer; transition: background var(--transition-fast); }
.note-card:hover { background: var(--color-bg); }
.note-card.active { background: var(--color-primary-light); border-left: 3px solid var(--color-primary); }
.note-title { display: flex; align-items: center; gap: 4px; font-size: 15px; font-weight: 500; color: var(--color-text-primary); margin-bottom: 4px; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
.pin-icon { flex-shrink: 0; color: var(--color-warning); }
.title-text { overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
.note-summary { font-size: 13px; color: var(--color-text-tertiary); margin-bottom: 6px; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
.note-meta { display: flex; justify-content: space-between; align-items: center; }
.update-time { font-size: 12px; color: var(--color-text-tertiary); }
.note-tags { display: flex; gap: 4px; }
.mini-tag { font-size: 11px; color: var(--color-primary-hover); background: var(--color-primary-light); padding: 2px 6px; border-radius: var(--radius-full); }
.empty-state { text-align: center; color: var(--color-text-tertiary); padding: 40px var(--space-4); font-size: 14px; }
.context-menu { position: fixed; z-index: 1000; background: var(--color-bg-card); border: 1px solid var(--color-border); border-radius: var(--radius-md); box-shadow: var(--shadow-md); overflow: hidden; min-width: 140px; }
.ctx-item { display: flex; align-items: center; gap: var(--space-2); width: 100%; padding: 10px var(--space-4); cursor: pointer; font-size: 13px; text-align: left; color: var(--color-text-primary); transition: background var(--transition-fast); }
.ctx-item:hover { background: var(--color-primary-bg); }
.ctx-danger:hover { background: var(--color-danger-light); color: var(--color-danger); }
:deep(.search-highlight) { background: #fef3c7; color: #92400e; padding: 0 2px; border-radius: 2px; font-weight: 600; }
.spin { animation: spin 0.8s linear infinite; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
@media (max-width: 768px) { .note-list { width: 100%; } }
</style>
