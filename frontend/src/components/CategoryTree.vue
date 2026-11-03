<template>
  <div class="category-tree">
    <div v-if="!visibleNodes.length" class="empty-hint">暂无分类</div>

    <div
      v-for="node in visibleNodes"
      :key="node.id"
      class="category-row"
      :class="{ active: selectedId === node.id }"
      :style="{ paddingLeft: node.depth * 16 + 8 + 'px' }"
      @click="onSelect(node.id)"
      @dblclick.stop="startRename(node)"
    >
      <span class="expand-icon" @click.stop="toggleExpand(node.id)">
        <template v-if="hasChildren(node.id)">
          <Icon :name="isExpanded(node.id) ? 'chevron-down' : 'chevron-right'" :size="12" />
        </template>
      </span>

      <input
        v-if="editingId === node.id"
        v-model="editingName"
        class="rename-input"
        @click.stop
        @keydown.enter="confirmRename"
        @keydown.esc="cancelRename"
        @blur="confirmRename"
      />
      <span v-else class="cat-name">{{ node.name }}</span>

      <span v-if="editingId !== node.id" class="cat-actions">
        <button class="action-btn" title="新建子分类" aria-label="新建子分类" @click.stop="emit('add-sub', node.id)">
          <Icon name="plus" :size="12" />
        </button>
        <button class="action-btn" title="重命名" aria-label="重命名" @click.stop="startRename(node)">
          <Icon name="edit" :size="12" />
        </button>
        <button class="action-btn del" title="删除" aria-label="删除" @click.stop="onDelete(node)">
          <Icon name="x" :size="12" />
        </button>
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import Icon from '@/components/Icon.vue'
import type { Category } from '@/types'

const props = withDefaults(
  defineProps<{ categories: Category[]; selectedId?: number }>(),
  {}
)

const emit = defineEmits<{
  (e: 'select', id: number): void
  (e: 'rename', id: number, name: string): void
  (e: 'delete', cat: Category): void
  (e: 'add-sub', parentId: number): void
}>()

const tree = computed<Category[]>(() => {
  const map = new Map<number, Category>()
  props.categories.forEach((c) => map.set(c.id, { ...c, children: [] }))
  const roots: Category[] = []
  map.forEach((c) => { if (c.parent_id && map.has(c.parent_id)) map.get(c.parent_id)!.children!.push(c); else roots.push(c) })
  return roots
})

const expandedIds = ref<Set<number>>(new Set())
function isExpanded(id: number) { return expandedIds.value.has(id) }
function toggleExpand(id: number) {
  const s = new Set(expandedIds.value)
  if (s.has(id)) s.delete(id); else s.add(id)
  expandedIds.value = s
}
function findNodeById(id: number): Category | undefined {
  function search(nodes: Category[]): Category | undefined {
    for (const n of nodes) { if (n.id === id) return n; if (n.children?.length) { const f = search(n.children); if (f) return f } }
    return undefined
  }
  return search(tree.value)
}
function hasChildren(id: number) { return !!findNodeById(id)?.children?.length }

const visibleNodes = computed<Array<Category & { depth: number }>>(() => {
  const result: Array<Category & { depth: number }> = []
  function traverse(nodes: Category[], depth: number) {
    for (const n of nodes) { result.push({ ...n, depth }); if (n.children?.length && isExpanded(n.id)) traverse(n.children, depth + 1) }
  }
  traverse(tree.value, 0); return result
})

function initExpanded() {
  const s = new Set<number>()
  function traverse(nodes: Category[]) { for (const n of nodes) { if (n.children?.length) { s.add(n.id); traverse(n.children) } } }
  traverse(tree.value); expandedIds.value = s
}
watch(tree, initExpanded, { immediate: true })

function onSelect(id: number) { emit('select', id) }

const editingId = ref<number | null>(null)
const editingName = ref('')
async function startRename(node: Category) {
  editingId.value = node.id; editingName.value = node.name
  await nextTick()
  const input = document.querySelector('.rename-input') as HTMLInputElement
  input?.focus(); input?.select()
}
function confirmRename() {
  if (editingId.value === null) return
  const trimmed = editingName.value.trim()
  if (trimmed) emit('rename', editingId.value, trimmed)
  editingId.value = null; editingName.value = ''
}
function cancelRename() { editingId.value = null; editingName.value = '' }
function onDelete(cat: Category) { emit('delete', cat) }
</script>

<style scoped>
.category-tree { user-select: none; }
.category-row { display: flex; align-items: center; gap: 4px; padding: 5px 8px; border-radius: var(--radius-md); cursor: pointer; font-size: 14px; position: relative; transition: background var(--transition-fast); min-height: 32px; }
.category-row:hover { background: var(--color-sidebar-hover); }
.category-row.active { background: var(--color-primary); }
.category-row.active .cat-name { color: var(--color-sidebar-text-bright); font-weight: 500; }
.category-row:active { transform: scale(0.98); }
.expand-icon { width: 16px; text-align: center; flex-shrink: 0; cursor: pointer; display: flex; align-items: center; justify-content: center; color: var(--color-sidebar-text-muted); }
.expand-icon:hover { color: #fff; }
.cat-name { flex: 1; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
.rename-input { flex: 1; padding: 2px 6px; border: 1px solid var(--color-primary); border-radius: var(--radius-sm); font-size: 14px; background: var(--color-bg-deep); color: var(--color-sidebar-text-bright); outline: none; min-width: 0; }
.cat-actions { display: none; gap: 2px; flex-shrink: 0; }
.category-row:hover .cat-actions { display: flex; }
.action-btn { border: none; background: none; cursor: pointer; display: flex; align-items: center; justify-content: center; color: var(--color-sidebar-text-muted); padding: 4px; border-radius: var(--radius-sm); line-height: 1; transition: all var(--transition-fast); }
.action-btn:hover { background: rgba(255, 255, 255, 0.15); color: var(--color-sidebar-text-bright); }
.action-btn:active { transform: scale(0.88); }
.action-btn.del:hover { color: var(--color-danger); background: rgba(231, 76, 60, 0.15); }
.empty-hint { padding: 6px 8px; font-size: 13px; color: var(--color-sidebar-text-muted); }
</style>
