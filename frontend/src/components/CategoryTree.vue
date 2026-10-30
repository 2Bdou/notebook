<template>
  <div class="category-tree">
    <div v-if="!visibleNodes.length" class="empty-hint">暂无分类</div>

    <!-- 扁平化渲染所有可见节点 -->
    <div
      v-for="node in visibleNodes"
      :key="node.id"
      class="category-row"
      :class="{ active: selectedId === node.id }"
      :style="{ paddingLeft: node.depth * 16 + 8 + 'px' }"
      @click="onSelect(node.id)"
      @dblclick.stop="startRename(node)"
    >
      <!-- 展开/折叠箭头 -->
      <span class="expand-icon" @click.stop="toggleExpand(node.id)">
        <template v-if="hasChildren(node.id)">
          {{ isExpanded(node.id) ? '▼' : '▶' }}
        </template>
      </span>

      <!-- 内联重命名输入框 / 分类名称 -->
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

      <!-- 悬停操作按钮 -->
      <span v-if="editingId !== node.id" class="cat-actions">
        <button class="action-btn" title="新建子分类" @click.stop="emit('add-sub', node.id)">＋</button>
        <button class="action-btn" title="重命名" @click.stop="startRename(node)">✎</button>
        <button class="action-btn del" title="删除" @click.stop="onDelete(node)">✕</button>
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import type { Category } from '@/types'

const props = withDefaults(
  defineProps<{
    /** 平铺分类列表 */
    categories: Category[]
    /** 当前选中的分类 ID */
    selectedId?: number
  }>(),
  {}
)

const emit = defineEmits<{
  (e: 'select', id: number): void
  (e: 'rename', id: number, name: string): void
  (e: 'delete', cat: Category): void
  (e: 'add-sub', parentId: number): void
}>()

// ==================== 树形构建 ====================
// 将平铺列表构建为树形结构
const tree = computed<Category[]>(() => {
  const map = new Map<number, Category>()
  props.categories.forEach((c) => map.set(c.id, { ...c, children: [] }))
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

// ==================== 展开/折叠状态 ====================
const expandedIds = ref<Set<number>>(new Set())

/** 判断节点是否展开 */
function isExpanded(id: number): boolean {
  return expandedIds.value.has(id)
}

/** 切换展开/折叠 */
function toggleExpand(id: number) {
  const s = new Set(expandedIds.value)
  if (s.has(id)) s.delete(id)
  else s.add(id)
  expandedIds.value = s
}

/** 在树中递归查找节点 */
function findNodeById(id: number): Category | undefined {
  function search(nodes: Category[]): Category | undefined {
    for (const n of nodes) {
      if (n.id === id) return n
      if (n.children?.length) {
        const found = search(n.children)
        if (found) return found
      }
    }
    return undefined
  }
  return search(tree.value)
}

/** 判断节点是否有子分类 */
function hasChildren(id: number): boolean {
  return !!findNodeById(id)?.children?.length
}

// ==================== 可见节点扁平化 ====================
// 根据展开状态将树展平为带 depth 的列表
const visibleNodes = computed<Array<Category & { depth: number }>>(() => {
  const result: Array<Category & { depth: number }> = []
  function traverse(nodes: Category[], depth: number) {
    for (const n of nodes) {
      result.push({ ...n, depth })
      if (n.children?.length && isExpanded(n.id)) {
        traverse(n.children, depth + 1)
      }
    }
  }
  traverse(tree.value, 0)
  return result
})

// 初始化：默认展开所有有子节点的分类
function initExpanded() {
  const s = new Set<number>()
  function traverse(nodes: Category[]) {
    for (const n of nodes) {
      if (n.children?.length) {
        s.add(n.id)
        traverse(n.children)
      }
    }
  }
  traverse(tree.value)
  expandedIds.value = s
}
// 树变化时重新初始化展开状态
watch(tree, initExpanded, { immediate: true })

// ==================== 选中分类 ====================
function onSelect(id: number) {
  emit('select', id)
}

// ==================== 内联重命名 ====================
const editingId = ref<number | null>(null)
const editingName = ref('')

/** 进入重命名模式 */
async function startRename(node: Category) {
  editingId.value = node.id
  editingName.value = node.name
  await nextTick()
  // 聚焦并选中输入框文本
  const input = document.querySelector('.rename-input') as HTMLInputElement
  input?.focus()
  input?.select()
}

/** 确认重命名 */
function confirmRename() {
  if (editingId.value === null) return
  const trimmed = editingName.value.trim()
  if (trimmed) {
    emit('rename', editingId.value, trimmed)
  }
  editingId.value = null
  editingName.value = ''
}

/** 取消重命名 */
function cancelRename() {
  editingId.value = null
  editingName.value = ''
}

// ==================== 删除分类 ====================
function onDelete(cat: Category) {
  emit('delete', cat)
}
</script>

<style scoped>
.category-tree {
  user-select: none;
}
.category-row {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 5px 8px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  position: relative;
  transition: background 0.15s;
}
.category-row:hover {
  background: #34495e;
}
.category-row.active {
  background: #42b983;
}
.category-row.active .cat-name {
  color: #fff;
  font-weight: 500;
}
/* 展开/折叠箭头 */
.expand-icon {
  width: 16px;
  text-align: center;
  font-size: 10px;
  color: #95a5a6;
  flex-shrink: 0;
  cursor: pointer;
}
.expand-icon:hover {
  color: #fff;
}
/* 分类名称 */
.cat-name {
  flex: 1;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
/* 内联重命名输入框 */
.rename-input {
  flex: 1;
  padding: 2px 6px;
  border: 1px solid #42b983;
  border-radius: 3px;
  font-size: 14px;
  background: #fff;
  color: #333;
  outline: none;
  min-width: 0;
}
/* 悬停操作按钮 */
.cat-actions {
  display: none;
  gap: 2px;
  flex-shrink: 0;
}
.category-row:hover .cat-actions {
  display: flex;
}
.action-btn {
  border: none;
  background: none;
  cursor: pointer;
  font-size: 12px;
  color: #bdc3c7;
  padding: 2px 4px;
  border-radius: 3px;
  line-height: 1;
}
.action-btn:hover {
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
}
.action-btn.del:hover {
  color: #e74c3c;
}
/* 空提示 */
.empty-hint {
  padding: 6px 8px;
  font-size: 13px;
  color: #7f8c8d;
}
</style>
