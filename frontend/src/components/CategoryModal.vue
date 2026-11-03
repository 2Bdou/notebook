<template>
  <div class="modal-overlay" @click.self="$emit('cancel')">
    <div class="modal-box">
      <div class="modal-header">
        <span class="modal-title">{{ isEdit ? '编辑分类' : '新建分类' }}</span>
        <button class="modal-close" aria-label="关闭" @click="$emit('cancel')">
          <Icon name="x" :size="18" />
        </button>
      </div>
      <div class="modal-body">
        <div class="form-field">
          <label class="field-label" for="cat-name-input">分类名称</label>
          <input
            id="cat-name-input"
            ref="nameInput"
            v-model="name"
            class="field-input"
            placeholder="请输入分类名称"
            maxlength="50"
            @keydown.enter="handleConfirm"
          />
        </div>
        <div class="form-field">
          <label class="field-label">父分类</label>
          <div class="parent-select" @click="showDropdown = !showDropdown">
            <span class="parent-label">{{ parentLabel }}</span>
            <Icon :name="showDropdown ? 'chevron-up' : 'chevron-down'" :size="12" class="dropdown-arrow" />
          </div>
          <div v-if="showDropdown" class="parent-dropdown">
            <div class="dropdown-item" :class="{ selected: parentId === null }" @click.stop="selectParent(null)">无（根分类）</div>
            <div
              v-for="node in parentOptions"
              :key="node.id"
              class="dropdown-item"
              :class="{ selected: parentId === node.id }"
              :style="{ paddingLeft: node.depth * 16 + 12 + 'px' }"
              @click.stop="selectParent(node.id)"
            >{{ node.name }}</div>
          </div>
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn-cancel" @click="$emit('cancel')">取消</button>
        <button class="btn-confirm" :disabled="!name.trim()" @click="handleConfirm">{{ isEdit ? '保存' : '创建' }}</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import Icon from '@/components/Icon.vue'
import type { Category } from '@/types'

const props = withDefaults(defineProps<{ category?: Category | null; categories: Category[] }>(), { category: null })
const emit = defineEmits<{ (e: 'confirm', data: { name: string; parent_id: number | null }): void; (e: 'cancel'): void }>()

const isEdit = computed(() => !!props.category)
const name = ref(props.category?.name || '')
const parentId = ref<number | null>(props.category?.parent_id ?? null)
const showDropdown = ref(false)
const nameInput = ref<HTMLInputElement | null>(null)

const parentLabel = computed(() => {
  if (parentId.value === null) return '无（根分类）'
  return props.categories.find((c) => c.id === parentId.value)?.name || '无（根分类）'
})

const parentOptions = computed(() => {
  const excludeIds = new Set<number>()
  if (props.category) {
    excludeIds.add(props.category.id)
    let changed = true
    while (changed) { changed = false; for (const c of props.categories) { if (c.parent_id && excludeIds.has(c.parent_id) && !excludeIds.has(c.id)) { excludeIds.add(c.id); changed = true } } }
  }
  const map = new Map<number, Category>()
  props.categories.filter((c) => !excludeIds.has(c.id)).forEach((c) => map.set(c.id, { ...c, children: [] }))
  const roots: Category[] = []
  map.forEach((c) => { if (c.parent_id && map.has(c.parent_id)) map.get(c.parent_id)!.children!.push(c); else roots.push(c) })
  const result: Array<Category & { depth: number }> = []
  function traverse(nodes: Category[], depth: number) { for (const n of nodes) { result.push({ ...n, depth }); if (n.children?.length) traverse(n.children, depth + 1) } }
  traverse(roots, 0); return result
})

function selectParent(id: number | null) { parentId.value = id; showDropdown.value = false }
function handleConfirm() { const t = name.value.trim(); if (!t) return; emit('confirm', { name: t, parent_id: parentId.value }) }
onMounted(() => { nextTick(() => nameInput.value?.focus()) })
</script>

<style scoped>
.modal-overlay { position: fixed; inset: 0; background: rgba(0, 0, 0, 0.5); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal-box { width: 400px; background: var(--color-bg-card); border-radius: var(--radius-lg); box-shadow: var(--shadow-lg); overflow: hidden; }
.modal-header { display: flex; align-items: center; justify-content: space-between; padding: var(--space-4) var(--space-5); border-bottom: 1px solid var(--color-border); }
.modal-title { font-size: 16px; font-weight: 600; color: var(--color-text-primary); }
.modal-close { border: none; background: none; cursor: pointer; color: var(--color-text-tertiary); display: flex; align-items: center; justify-content: center; width: 40px; height: 40px; padding: 4px; border-radius: var(--radius-sm); transition: all var(--transition-fast); touch-action: manipulation; }
.modal-close:hover { color: var(--color-text-primary); background: var(--color-bg); }
.modal-close:active { transform: scale(0.92); }
.modal-body { padding: var(--space-5); }
.form-field { margin-bottom: var(--space-4); }
.field-label { display: block; font-size: 13px; color: var(--color-text-secondary); margin-bottom: 6px; font-weight: 500; }
.field-input { width: 100%; padding: 10px 12px; border: 1px solid var(--color-border); border-radius: var(--radius-md); font-size: 14px; box-sizing: border-box; background: var(--color-bg-card); color: var(--color-text-primary); transition: border-color var(--transition-fast); }
.field-input:focus { border-color: var(--color-primary); outline: none; box-shadow: 0 0 0 3px var(--color-primary-bg); }
.parent-select { display: flex; align-items: center; justify-content: space-between; padding: 10px 12px; border: 1px solid var(--color-border); border-radius: var(--radius-md); cursor: pointer; font-size: 14px; background: var(--color-bg-card); color: var(--color-text-primary); transition: border-color var(--transition-fast); }
.parent-select:hover { border-color: var(--color-primary); }
.parent-select:active { border-color: var(--color-primary); }
.dropdown-arrow { color: var(--color-text-tertiary); flex-shrink: 0; }
.parent-dropdown { margin-top: 4px; border: 1px solid var(--color-border); border-radius: var(--radius-md); max-height: 200px; overflow-y: auto; background: var(--color-bg-card); box-shadow: var(--shadow-md); }
.dropdown-item { padding: 8px 12px; font-size: 14px; cursor: pointer; white-space: nowrap; color: var(--color-text-primary); transition: background var(--transition-fast); min-height: 44px; display: flex; align-items: center; touch-action: manipulation; }
.dropdown-item:hover { background: var(--color-primary-bg); }
.dropdown-item:active { background: var(--color-primary-light); }
.dropdown-item.selected { background: var(--color-primary-light); color: var(--color-primary-hover); font-weight: 500; }
.modal-footer { display: flex; justify-content: flex-end; gap: var(--space-2); padding: var(--space-3) var(--space-5); border-top: 1px solid var(--color-border); }
.btn-cancel, .btn-confirm { padding: 10px 20px; border-radius: var(--radius-md); font-size: 14px; cursor: pointer; border: none; font-weight: 500; transition: all var(--transition-fast); min-height: 44px; touch-action: manipulation; }
.btn-cancel:active { transform: scale(0.96); }
.btn-confirm:active:not(:disabled) { transform: scale(0.96); }
.btn-cancel { background: var(--color-bg); color: var(--color-text-secondary); }
.btn-cancel:hover { background: var(--color-border-light); }
.btn-confirm { background: var(--color-primary); color: #fff; }
.btn-confirm:hover { background: var(--color-primary-hover); }
.btn-confirm:disabled { background: var(--color-primary-light); color: var(--color-primary); cursor: not-allowed; opacity: 0.6; }

/* ====== 移动端：输入字号 ≥16px + 触摸目标 ≥44px ====== */
@media (max-width: 768px) {
  .field-input {
    font-size: 16px;
    min-height: 44px;
  }
  .parent-select {
    min-height: 44px;
  }
}
</style>
