<template>
  <div class="modal-overlay" @click.self="$emit('cancel')">
    <div class="modal-box">
      <!-- 弹窗标题 -->
      <div class="modal-header">
        <span class="modal-title">{{ isEdit ? '编辑分类' : '新建分类' }}</span>
        <button class="modal-close" @click="$emit('cancel')">×</button>
      </div>

      <!-- 表单内容 -->
      <div class="modal-body">
        <!-- 分类名称 -->
        <div class="form-field">
          <label class="field-label">分类名称</label>
          <input
            ref="nameInput"
            v-model="name"
            class="field-input"
            placeholder="请输入分类名称"
            maxlength="50"
            @keydown.enter="handleConfirm"
          />
        </div>

        <!-- 父分类选择（树形下拉） -->
        <div class="form-field">
          <label class="field-label">父分类</label>
          <div class="parent-select" @click="showDropdown = !showDropdown">
            <span class="parent-label">{{ parentLabel }}</span>
            <span class="dropdown-arrow">{{ showDropdown ? '▲' : '▼' }}</span>
          </div>
          <!-- 下拉树形列表 -->
          <div v-if="showDropdown" class="parent-dropdown">
            <!-- "无"选项 — 作为根分类 -->
            <div
              class="dropdown-item"
              :class="{ selected: parentId === null }"
              @click.stop="selectParent(null)"
            >
              无（根分类）
            </div>
            <!-- 递归渲染可选分类（排除当前编辑的分类及其子分类） -->
            <div
              v-for="node in parentOptions"
              :key="node.id"
              class="dropdown-item"
              :class="{ selected: parentId === node.id }"
              :style="{ paddingLeft: node.depth * 16 + 12 + 'px' }"
              @click.stop="selectParent(node.id)"
            >
              {{ node.name }}
            </div>
          </div>
        </div>
      </div>

      <!-- 底部操作按钮 -->
      <div class="modal-footer">
        <button class="btn-cancel" @click="$emit('cancel')">取消</button>
        <button class="btn-confirm" :disabled="!name.trim()" @click="handleConfirm">
          {{ isEdit ? '保存' : '创建' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import type { Category } from '@/types'

const props = withDefaults(
  defineProps<{
    /** 编辑模式时传入已有分类 */
    category?: Category | null
    /** 全部分类列表（用于父分类选择） */
    categories: Category[]
  }>(),
  { category: null }
)

const emit = defineEmits<{
  (e: 'confirm', data: { name: string; parent_id: number | null }): void
  (e: 'cancel'): void
}>()

// 是否为编辑模式
const isEdit = computed(() => !!props.category)

// 表单状态
const name = ref(props.category?.name || '')
const parentId = ref<number | null>(props.category?.parent_id ?? null)
const showDropdown = ref(false)
const nameInput = ref<HTMLInputElement | null>(null)

// 父分类显示文本
const parentLabel = computed(() => {
  if (parentId.value === null) return '无（根分类）'
  const cat = props.categories.find((c) => c.id === parentId.value)
  return cat?.name || '无（根分类）'
})

/**
 * 构建父分类可选项的扁平列表（排除当前编辑分类及其子分类，防止循环引用）
 */
const parentOptions = computed(() => {
  // 收集当前编辑分类的所有子分类 ID（含多层）
  const excludeIds = new Set<number>()
  if (props.category) {
    excludeIds.add(props.category.id)
    let changed = true
    while (changed) {
      changed = false
      for (const c of props.categories) {
        if (c.parent_id && excludeIds.has(c.parent_id) && !excludeIds.has(c.id)) {
          excludeIds.add(c.id)
          changed = true
        }
      }
    }
  }

  // 构建树并展平为带 depth 的列表
  const map = new Map<number, Category>()
  props.categories
    .filter((c) => !excludeIds.has(c.id))
    .forEach((c) => map.set(c.id, { ...c, children: [] }))

  const roots: Category[] = []
  map.forEach((c) => {
    if (c.parent_id && map.has(c.parent_id)) {
      map.get(c.parent_id)!.children!.push(c)
    } else {
      roots.push(c)
    }
  })

  const result: Array<Category & { depth: number }> = []
  function traverse(nodes: Category[], depth: number) {
    for (const n of nodes) {
      result.push({ ...n, depth })
      if (n.children?.length) traverse(n.children, depth + 1)
    }
  }
  traverse(roots, 0)
  return result
})

/** 选择父分类 */
function selectParent(id: number | null) {
  parentId.value = id
  showDropdown.value = false
}

/** 确认提交 */
function handleConfirm() {
  const trimmed = name.value.trim()
  if (!trimmed) return
  emit('confirm', { name: trimmed, parent_id: parentId.value })
}

// 挂载后自动聚焦输入框
onMounted(() => {
  nextTick(() => nameInput.value?.focus())
})
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.modal-box {
  width: 400px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  overflow: hidden;
}
.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #eee;
}
.modal-title {
  font-size: 16px;
  font-weight: 600;
}
.modal-close {
  border: none;
  background: none;
  font-size: 20px;
  cursor: pointer;
  color: #999;
  line-height: 1;
}
.modal-close:hover {
  color: #333;
}
.modal-body {
  padding: 20px;
}
.form-field {
  margin-bottom: 16px;
}
.field-label {
  display: block;
  font-size: 13px;
  color: #666;
  margin-bottom: 6px;
}
.field-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  box-sizing: border-box;
}
.field-input:focus {
  border-color: #42b983;
  outline: none;
}
/* 父分类下拉选择器 */
.parent-select {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}
.parent-select:hover {
  border-color: #42b983;
}
.dropdown-arrow {
  font-size: 10px;
  color: #999;
}
.parent-dropdown {
  margin-top: 4px;
  border: 1px solid #ddd;
  border-radius: 4px;
  max-height: 200px;
  overflow-y: auto;
  background: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}
.dropdown-item {
  padding: 6px 12px;
  font-size: 14px;
  cursor: pointer;
  white-space: nowrap;
}
.dropdown-item:hover {
  background: #f0f7f4;
}
.dropdown-item.selected {
  background: #e8f5e9;
  color: #42b983;
  font-weight: 500;
}
/* 底部按钮 */
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 12px 20px;
  border-top: 1px solid #eee;
}
.btn-cancel,
.btn-confirm {
  padding: 8px 20px;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  border: none;
}
.btn-cancel {
  background: #f5f5f5;
  color: #666;
}
.btn-cancel:hover {
  background: #e0e0e0;
}
.btn-confirm {
  background: #42b983;
  color: #fff;
}
.btn-confirm:hover {
  background: #369870;
}
.btn-confirm:disabled {
  background: #a5d6b8;
  cursor: not-allowed;
}
</style>
