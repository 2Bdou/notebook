<template>
  <div class="note-list">
    <!-- ====== 手机端：紧凑工具栏（3 行） ====== -->
    <div v-if="isMobile" class="mobile-toolbar">
      <!-- 第 1 行：logo + 新建 + 用户 -->
      <div class="mobile-top-bar">
        <div class="mobile-brand">
          <Icon name="notebook" :size="18" :stroke-width="1.8" class="logo-icon" />
          <span class="mobile-logo">记事本</span>
        </div>
        <button class="mobile-btn-new" @click="$emit('new')" aria-label="新建笔记">
          <Icon name="plus" :size="16" />
          <span>新建</span>
        </button>
      </div>

      <!-- 第 2 行：搜索框 -->
      <div class="search-bar">
        <Icon name="search" :size="16" class="search-icon" />
        <input v-model="keyword" class="search-input" placeholder="搜索笔记..." aria-label="搜索笔记" @input="onSearch" />
        <Icon v-if="noteStore.searching" name="loader" :size="16" class="search-loading spin" />
      </div>

      <!-- 第 3 行：分类 + 标签 + 排序 下拉选择器 -->
      <div class="mobile-filter-row">
        <select class="mobile-filter-select" aria-label="筛选分类" :value="noteStore.filter.category_id ?? ''" @change="onMobileCategoryChange">
          <option value="">全部分类</option>
          <option v-for="cat in flatCategories" :key="cat.id" :value="cat.id">{{ cat.label }}</option>
        </select>
        <select class="mobile-filter-select" aria-label="筛选标签" :value="noteStore.filter.tag_id ?? ''" @change="onMobileTagChange">
          <option value="">全部标签</option>
          <option v-for="tag in tagStore.tags" :key="tag.id" :value="tag.id">{{ tag.name }} ({{ tag.note_count }})</option>
        </select>
        <select class="mobile-filter-select" aria-label="排序" :value="noteStore.filter.sort + '-' + noteStore.filter.order" @change="onMobileSortChange">
          <option value="updated_at-desc">更新↓</option>
          <option value="updated_at-asc">更新↑</option>
          <option value="created_at-desc">创建↓</option>
          <option value="title-asc">标题A-Z</option>
          <option value="title-desc">标题Z-A</option>
        </select>
      </div>
    </div>


    <!-- ====== 桌面端：搜索框 + 排序栏 ====== -->
    <template v-if="!isMobile">
      <div class="search-bar">
        <Icon name="search" :size="16" class="search-icon" />
        <input v-model="keyword" class="search-input" placeholder="搜索笔记...（至少 2 个字符）"
          aria-label="搜索笔记" @input="onSearch" />
        <Icon v-if="noteStore.searching" name="loader" :size="16" class="search-loading spin" />
      </div>
      <div class="sort-bar">
        <select class="sort-select" aria-label="排序方式" :value="noteStore.filter.sort" @change="onSortChange">
          <option value="updated_at">更新时间</option>
          <option value="created_at">创建时间</option>
          <option value="title">标题</option>
          <option value="word_count">字数</option>
        </select>
        <button class="sort-order-btn" :aria-label="noteStore.filter.order === 'desc' ? '降序' : '升序'" @click="toggleOrder">
          <Icon :name="noteStore.filter.order === 'desc' ? 'arrow-down' : 'arrow-up'" :size="14" />
        </button>
      </div>
    </template>

    <!-- ====== 过滤条件（共用） ====== -->
    <div v-if="noteStore.hasFilter" class="filter-bar">
      <span v-if="noteStore.filter.category_id" class="filter-chip">
        分类: {{ categoryStore.getCategoryName(noteStore.filter.category_id) }}
        <button class="chip-close" aria-label="清除分类过滤" @click="noteStore.clearCategoryFilter()"><Icon name="x" :size="10" /></button>
      </span>
      <span v-if="noteStore.filter.tag_id" class="filter-chip">
        标签: {{ tagStore.getTagName(noteStore.filter.tag_id) }}
        <button class="chip-close" aria-label="清除标签过滤" @click="noteStore.clearTagFilter()"><Icon name="x" :size="10" /></button>
      </span>
      <span v-if="noteStore.filter.q" class="filter-chip">
        搜索: {{ noteStore.filter.q }}
        <button class="chip-close" aria-label="清除搜索" @click="clearSearch"><Icon name="x" :size="10" /></button>
      </span>
      <button class="btn-clear-all" @click="clearAllFilters">清除全部</button>
    </div>

    <!-- ====== 笔记卡片列表（共用） ====== -->
    <div class="list-body">
      <div v-if="noteStore.loading && !noteStore.notes.length" class="list-loading">加载中...</div>
      <template v-else>
        <template v-for="note in noteStore.notes" :key="note.id">
          <div v-if="showPinSeparator(note)" class="pin-separator">
            <span class="separator-text">普通笔记</span>
          </div>
          <div class="note-card" :class="{ active: noteStore.current?.id === note.id }"
            @click="selectNote(note)" @contextmenu.prevent="onContextMenu($event, note)">
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
          <template v-else>{{ noteStore.hasFilter ? '没有符合条件的笔记' : '暂无笔记，点击「新建笔记」开始记录' }}</template>
        </div>
      </template>
    </div>

    <!-- ====== 手机端底部 ====== -->
    <div v-if="isMobile" class="mobile-footer">
      <router-link to="/trash" class="trash-link">
        <Icon name="trash" :size="16" />
        <span>回收站</span>
      </router-link>
      <div class="user-info" v-if="authStore.user">
        <span class="user-avatar">{{ authStore.user.username.charAt(0).toUpperCase() }}</span>
        <span class="user-name">{{ authStore.user.username }}</span>
        <button class="btn-logout" title="退出登录" aria-label="退出登录" @click="handleLogout">
          <Icon name="logout" :size="16" />
        </button>
      </div>
    </div>

    <!-- 右键菜单 -->
    <div v-if="contextMenu.visible" class="context-menu"
      :style="{ top: contextMenu.y + 'px', left: contextMenu.x + 'px' }" @click.stop>
      <button class="ctx-item" @click="quickTogglePin">
        <Icon name="pin" :size="14" />
        <span>{{ contextMenu.note?.is_pinned ? '取消置顶' : '置顶' }}</span>
      </button>
      <button class="ctx-item ctx-danger" @click="quickDelete">
        <Icon name="trash" :size="14" />
        <span>删除</span>
      </button>
    </div>

    <!-- 分类弹窗 -->
    <CategoryModal v-if="modalVisible" :category="editingCategory" :categories="categoryStore.categories"
      @confirm="onModalConfirm" @cancel="modalVisible = false" />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import Icon from '@/components/Icon.vue'
import CategoryTree from '@/components/CategoryTree.vue'
import CategoryModal from '@/components/CategoryModal.vue'
import { useNoteStore } from '@/stores/note'
import { useCategoryStore } from '@/stores/category'
import { useTagStore } from '@/stores/tag'
import { useAuthStore } from '@/stores/auth'
import type { Note, SortField, SortOrder, Category, Tag } from '@/types'

const props = withDefaults(defineProps<{ isMobile?: boolean }>(), { isMobile: false })
const emit = defineEmits<{ (e: 'select-note'): void; (e: 'new'): void }>()

const noteStore = useNoteStore()
const categoryStore = useCategoryStore()
const tagStore = useTagStore()
const authStore = useAuthStore()
const router = useRouter()
const keyword = ref('')

// ====== 搜索 ======
let searchTimer: ReturnType<typeof setTimeout> | null = null
function onSearch() {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => { noteStore.setSearch(keyword.value) }, 300)
}
function clearSearch() { keyword.value = ''; noteStore.setSearch('') }
function clearAllFilters() { keyword.value = ''; noteStore.clearFilters() }

// ====== 排序 ======
function onSortChange(e: Event) { noteStore.setSort((e.target as HTMLSelectElement).value as SortField); saveSortState() }
function toggleOrder() { noteStore.setOrder(noteStore.filter.order === 'desc' ? 'asc' : 'desc'); saveSortState() }
function saveSortState() { localStorage.setItem('note_sort', noteStore.filter.sort); localStorage.setItem('note_order', noteStore.filter.order) }
function restoreSortState() {
  const s = localStorage.getItem('note_sort') as SortField | null
  const o = localStorage.getItem('note_order') as SortOrder | null
  if (s) noteStore.filter.sort = s
  if (o) noteStore.filter.order = o
}

// ====== 选择笔记 ======
function selectNote(note: Note) {
  noteStore.fetchNote(note.id)
  if (props.isMobile) emit('select-note')
}

// ====== 退出登录 ======
function handleLogout() { authStore.logout(); router.push({ name: 'login' }) }

// ====== 过滤状态 ======
const hasCategoryFilter = ref(false)
const hasTagFilter = ref(false)
watch(() => noteStore.filter, (f) => {
  hasCategoryFilter.value = f.category_id !== undefined
  hasTagFilter.value = f.tag_id !== undefined
}, { deep: true, immediate: true })
function showAllNotes() { noteStore.clearFilters() }

// ====== 折叠区（桌面端用） ======
const expandedSections = reactive({ category: false, tag: false })
function toggleSection(key: 'category' | 'tag') { expandedSections[key] = !expandedSections[key] }

// ====== 手机端：展平分类树为 select 选项 ======
const flatCategories = computed(() => {
  const result: { id: number; label: string }[] = []
  function flatten(cats: Category[], depth: number) {
    for (const c of cats) {
      result.push({ id: c.id, label: depth > 0 ? '┣ ' + '　'.repeat(depth - 1) + c.name : c.name })
      if (c.children?.length) flatten(c.children, depth + 1)
    }
  }
  flatten(categoryStore.categories, 0)
  return result
})

// ====== 手机端下拉选择器事件 ======
function onMobileCategoryChange(e: Event) {
  const val = (e.target as HTMLSelectElement).value
  noteStore.setCategoryFilter(val ? Number(val) : undefined)
}
function onMobileTagChange(e: Event) {
  const val = (e.target as HTMLSelectElement).value
  noteStore.setTagFilter(val ? Number(val) : undefined)
}
function onMobileSortChange(e: Event) {
  const val = (e.target as HTMLSelectElement).value
  const [sort, order] = val.split('-')
  noteStore.setSort(sort as SortField)
  noteStore.setOrder(order as SortOrder)
  saveSortState()
}

// ====== 分类操作 ======
const modalVisible = ref(false)
const editingCategory = ref<Category | null>(null)
const addSubParentId = ref<number | null>(null)
function openCreateCategory() { editingCategory.value = null; addSubParentId.value = null; modalVisible.value = true }
function onSelectCategory(id: number) { noteStore.setCategoryFilter(noteStore.filter.category_id === id ? undefined : id) }
async function onRenameCategory(id: number, name: string) {
  try { await categoryStore.updateCategory(id, { name }) } catch (e: any) { alert(e?.message || '重命名失败') }
}
async function onDeleteCategory(cat: Category) {
  if (!confirm(`确定删除分类「${cat.name}」？`)) return
  try { await categoryStore.deleteCategory(cat.id); if (noteStore.filter.category_id === cat.id) noteStore.clearCategoryFilter() }
  catch (e: any) { alert(e?.message || '删除失败') }
}
function onAddSubCategory(parentId: number) { editingCategory.value = null; addSubParentId.value = parentId; modalVisible.value = true }
async function onModalConfirm(data: { name: string; parent_id: number | null }) {
  try {
    if (editingCategory.value) await categoryStore.updateCategory(editingCategory.value.id, { name: data.name, parent_id: data.parent_id })
    else await categoryStore.createCategory({ name: data.name, parent_id: addSubParentId.value ?? data.parent_id })
    modalVisible.value = false; editingCategory.value = null; addSubParentId.value = null
  } catch (e: any) { alert(e?.message || '操作失败') }
}

// ====== 标签操作 ======
const tagCreating = ref(false)
const newTagName = ref('')
function openCreateTag() { tagCreating.value = true; newTagName.value = '' }
async function confirmCreateTag() {
  const name = newTagName.value.trim()
  if (!name) { tagCreating.value = false; return }
  try { await tagStore.createTag(name) } catch (e: any) { alert(e?.message || '创建失败') }
  tagCreating.value = false; newTagName.value = ''
}
function cancelCreateTag() { tagCreating.value = false; newTagName.value = '' }
function onSelectTag(id: number) { noteStore.setTagFilter(noteStore.filter.tag_id === id ? undefined : id) }
async function onDeleteTag(tag: Tag) {
  if (!confirm(`确定删除标签「${tag.name}」？`)) return
  try { await tagStore.deleteTag(tag.id); if (noteStore.filter.tag_id === tag.id) noteStore.clearTagFilter() }
  catch (e: any) { alert(e?.message || '删除失败') }
}

// ====== 搜索高亮 ======
function escapeHtml(t: string): string { return t.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;') }
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

// ====== 右键菜单 ======
const contextMenu = ref({ visible: false, x: 0, y: 0, note: null as Note | null })
function onContextMenu(e: MouseEvent, note: Note) { contextMenu.value = { visible: true, x: e.clientX, y: e.clientY, note } }
function closeContextMenu() { contextMenu.value.visible = false }
async function quickTogglePin() {
  const note = contextMenu.value.note; if (!note) return; closeContextMenu()
  try {
    const pinned = !note.is_pinned
    await noteStore.updateNote(note.id, { is_pinned: pinned })
    const t = noteStore.notes.find((n) => n.id === note.id); if (t) t.is_pinned = pinned
    if (noteStore.current?.id === note.id) noteStore.current.is_pinned = pinned
    await noteStore.fetchNotes()
  } catch (e: any) { alert(e?.message || '操作失败') }
}
async function quickDelete() {
  const note = contextMenu.value.note; if (!note) return; closeContextMenu()
  if (!confirm(`确定删除「${note.title || '无标题'}」？`)) return
  try { await noteStore.deleteNote(note.id); if (noteStore.current?.id === note.id) noteStore.current = null; await noteStore.fetchNotes() }
  catch (e: any) { alert(e?.message || '删除失败') }
}

// ====== 工具函数 ======
function getSummary(content: string): string { return content.replace(/[#*`>\-\[\]()!]/g, '').trim().slice(0, 80) || '无内容' }
function formatDate(dateStr: string): string {
  const d = new Date(dateStr.replace(' ', 'T'))
  const diff = Date.now() - d.getTime()
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return Math.floor(diff / 60000) + '分钟前'
  if (diff < 86400000) return Math.floor(diff / 3600000) + '小时前'
  return `${d.getMonth() + 1}月${d.getDate()}日`
}

// ====== 生命周期 ======
watch(() => noteStore.filter.q, (q) => { if (!q && keyword.value) keyword.value = '' })
onMounted(() => { restoreSortState(); document.addEventListener('click', closeContextMenu) })
onUnmounted(() => { document.removeEventListener('click', closeContextMenu) })
</script>

<style scoped>
.note-list { width: 320px; flex-shrink: 0; background: var(--color-bg-card); border-right: 1px solid var(--color-border); display: flex; flex-direction: column; overflow: hidden; }

/* ====== 手机端紧凑工具栏 ====== */
.mobile-toolbar { flex-shrink: 0; background: var(--color-bg-card); border-bottom: 1px solid var(--color-border); }
.mobile-top-bar { display: flex; align-items: center; gap: var(--space-2); padding: calc(var(--space-2) + env(safe-area-inset-top, 0px)) var(--space-3); background: var(--color-sidebar-bg); }
.mobile-brand { display: flex; align-items: center; gap: var(--space-2); flex: 1; }
.logo-icon { color: var(--color-primary); }
.mobile-logo { font-size: 16px; font-weight: 600; color: #f1f5f9; }
.mobile-btn-new { padding: 8px 14px; background: var(--color-primary); color: #fff; border-radius: var(--radius-md); font-size: 14px; font-weight: 500; display: flex; align-items: center; gap: 4px; min-height: 44px; border: none; cursor: pointer; flex-shrink: 0; }
.mobile-btn-new:active { transform: scale(0.96); }

/* 第 3 行：筛选下拉选择器 */
.mobile-filter-row { display: flex; gap: 8px; padding: 6px var(--space-3); background: var(--color-bg); border-bottom: 1px solid var(--color-border-light); }
.mobile-filter-select { flex: 1; padding: 8px 4px; border: 1px solid var(--color-border); border-radius: var(--radius-md); font-size: 16px; background: var(--color-bg-card); color: var(--color-text-primary); cursor: pointer; min-height: 44px; min-width: 0; }
.mobile-filter-select:active { border-color: var(--color-primary); }
.mobile-filter-select:focus-visible { border-color: var(--color-primary); outline: 2px solid var(--color-primary-bg); outline-offset: -1px; }

/* 标签列表 */
.tag-list { list-style: none; }
.tag-item { display: flex; align-items: center; gap: var(--space-2); padding: 10px 8px; border-radius: var(--radius-md); cursor: pointer; min-height: 44px; }
.tag-item:hover { background: var(--color-primary-bg); }
.tag-item.active { background: var(--color-primary); color: #fff; }
.tag-icon { flex-shrink: 0; opacity: 0.7; }
.tag-item.active .tag-icon { opacity: 1; }
.tag-name { font-size: 14px; flex: 1; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
.tag-right { display: flex; align-items: center; gap: 4px; flex-shrink: 0; }
.tag-count { font-size: 12px; color: var(--color-text-tertiary); background: var(--color-border-light); padding: 1px 6px; border-radius: var(--radius-full); min-width: 20px; text-align: center; }
.tag-item.active .tag-count { background: rgba(255,255,255,0.25); color: #fff; }
.tag-del { color: var(--color-text-secondary); padding: 8px; border-radius: var(--radius-sm); border: none; background: transparent; cursor: pointer; display: flex; align-items: center; justify-content: center; min-height: 44px; min-width: 44px; opacity: 0.5; }
.tag-item:hover .tag-del { opacity: 1; }
.tag-del:hover { color: var(--color-danger); background: var(--color-danger-light); opacity: 1; }
.tag-del:active { transform: scale(0.92); }
.tag-create-form { padding: 0 var(--space-2) 6px; }
.tag-input { width: 100%; padding: 10px 8px; border: 1px solid var(--color-primary); border-radius: var(--radius-md); font-size: 16px; background: var(--color-bg-card); color: var(--color-text-primary); box-sizing: border-box; min-height: 44px; }
.tag-input:focus { outline: none; box-shadow: 0 0 0 3px var(--color-primary-bg); }
.empty-hint { padding: 6px 8px; font-size: 13px; color: var(--color-text-tertiary); }

/* 手机端底部 */
.mobile-footer { margin-top: auto; padding: var(--space-3) var(--space-4); border-top: 1px solid var(--color-border); background: var(--color-bg-card); flex-shrink: 0; }
.trash-link { display: flex; align-items: center; gap: var(--space-2); font-size: 15px; color: var(--color-text-secondary); padding: 10px 0; min-height: 44px; }
.trash-link:hover { color: var(--color-primary); }
.user-info { display: flex; align-items: center; gap: var(--space-2); margin-top: var(--space-3); padding-top: var(--space-3); border-top: 1px solid var(--color-border-light); }
.user-avatar { width: 28px; height: 28px; border-radius: 50%; background: var(--color-primary); color: #fff; font-size: 14px; font-weight: 600; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.user-name { font-size: 14px; color: var(--color-text-primary); flex: 1; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
.btn-logout { color: var(--color-text-tertiary); padding: 10px; border-radius: var(--radius-md); display: flex; align-items: center; justify-content: center; min-height: 44px; min-width: 44px; border: none; background: transparent; cursor: pointer; }
.btn-logout:hover { color: var(--color-danger); background: var(--color-danger-light); }

/* ====== 搜索框 ====== */
.search-bar { padding: var(--space-3); border-bottom: 1px solid var(--color-border-light); display: flex; align-items: center; gap: var(--space-2); }
.search-icon { color: var(--color-text-tertiary); flex-shrink: 0; }
.search-input { flex: 1; padding: 10px 0; border: none; font-size: 16px; background: transparent; color: var(--color-text-primary); min-height: 44px; }
.search-input::placeholder { color: var(--color-text-tertiary); }
.search-loading { color: var(--color-text-tertiary); flex-shrink: 0; }

/* ====== 排序栏 ====== */
.sort-bar { display: flex; align-items: center; gap: 6px; padding: 6px var(--space-3); border-bottom: 1px solid var(--color-border-light); background: var(--color-bg); }
.sort-select { flex: 1; padding: 10px 8px; border: 1px solid var(--color-border); border-radius: var(--radius-md); font-size: 14px; background: var(--color-bg-card); color: var(--color-text-primary); cursor: pointer; min-height: 44px; }
.sort-select:focus { border-color: var(--color-primary); }
.sort-order-btn { padding: 10px; border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-bg-card); cursor: pointer; display: flex; align-items: center; justify-content: center; color: var(--color-text-secondary); min-height: 44px; min-width: 44px; }
.sort-order-btn:hover { border-color: var(--color-primary); color: var(--color-primary); }

/* ====== 过滤标签 ====== */
.filter-bar { display: flex; align-items: center; flex-wrap: wrap; gap: 6px; padding: 8px var(--space-3); border-bottom: 1px solid var(--color-border-light); background: var(--color-primary-bg); }
.filter-chip { display: inline-flex; align-items: center; gap: 4px; padding: 4px 8px; background: var(--color-primary-light); color: var(--color-primary-hover); border-radius: var(--radius-full); font-size: 12px; font-weight: 500; }
.chip-close { cursor: pointer; color: var(--color-primary-hover); padding: 8px; display: flex; align-items: center; opacity: 0.6; min-height: 44px; min-width: 44px; border: none; background: transparent; }
.chip-close:hover { opacity: 1; }
.btn-clear-all { cursor: pointer; font-size: 14px; color: var(--color-danger); padding: 8px 12px; margin-left: auto; min-height: 44px; border: none; background: transparent; }
.btn-clear-all:hover { text-decoration: underline; }

/* ====== 笔记列表 ====== */
.list-body { flex: 1; overflow-y: auto; }
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

/* ====== 右键菜单 ====== */
.context-menu { position: fixed; z-index: 1000; background: var(--color-bg-card); border: 1px solid var(--color-border); border-radius: var(--radius-md); box-shadow: var(--shadow-md); overflow: hidden; min-width: 140px; }
.ctx-item { display: flex; align-items: center; gap: var(--space-2); width: 100%; padding: 10px var(--space-4); cursor: pointer; font-size: 13px; text-align: left; color: var(--color-text-primary); }
.ctx-item:hover { background: var(--color-primary-bg); }
.ctx-danger:hover { background: var(--color-danger-light); color: var(--color-danger); }

/* ====== 搜索高亮 ====== */
:deep(.search-highlight) { background: #fef3c7; color: #92400e; padding: 0 2px; border-radius: 2px; font-weight: 600; }

/* ====== 加载动画 ====== */
.spin { animation: spin 0.8s linear infinite; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
@media (prefers-reduced-motion: reduce) {
  .spin { animation: none; }
}

/* ====== Focus states (focus-states rule) ====== */
.mobile-btn-new:focus-visible,
.mobile-filter-select:focus-visible,
.sort-order-btn:focus-visible,
.btn-logout:focus-visible,
.tag-del:focus-visible,
.chip-close:focus-visible,
.btn-clear-all:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

/* ====== Press feedback (press-feedback rule) ====== */
.note-card:active {
  transform: scale(0.98);
}

/* ====== Safe area insets (safe-area-awareness rule) ====== */
.mobile-footer {
  padding-bottom: calc(var(--space-3) + env(safe-area-inset-bottom, 0px));
}

/* ====== 手机端：全屏宽度 ====== */
@media (max-width: 768px) {
  .note-list { width: 100%; border-right: none; }
  .mobile-btn-new, .mobile-filter-select,
  .tag-item, .sort-order-btn, .note-card, .btn-logout, .tag-del, .chip-close {
    touch-action: manipulation;
  }
}
</style>
