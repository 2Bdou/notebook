<template>
  <aside class="sidebar">
    <!-- 顶部标题与新建按钮 -->
    <div class="sidebar-header">
      <h1 class="logo">📝 记事本</h1>
      <button class="btn-new" @click="$emit('new')">+ 新建笔记</button>
    </div>

    <!-- 全部笔记按钮 -->
    <div class="section">
      <div
        class="all-notes-btn"
        :class="{ active: !hasCategoryFilter && !hasTagFilter }"
        @click="showAllNotes"
      >
        📋 全部笔记
      </div>
    </div>

    <!-- 分类区 -->
    <div class="section">
      <div class="section-header">
        <span class="section-title">分类</span>
        <button class="btn-add" title="新建分类" @click="openCreateCategory">+</button>
      </div>
      <CategoryTree
        :categories="categoryStore.categories"
        :selected-id="noteStore.filter.category_id"
        @select="onSelectCategory"
        @rename="onRenameCategory"
        @delete="onDeleteCategory"
        @add-sub="onAddSubCategory"
      />
    </div>

    <!-- 标签区 -->
    <div class="section">
      <div class="section-header">
        <span class="section-title">标签</span>
        <button class="btn-add" title="新建标签" @click="openCreateTag">+</button>
      </div>
      <!-- 新建标签输入框 -->
      <div v-if="tagCreating" class="tag-create-form">
        <input
          v-model="newTagName"
          class="tag-input"
          placeholder="标签名称"
          maxlength="20"
          @keydown.enter="confirmCreateTag"
          @keydown.esc="cancelCreateTag"
          @blur="confirmCreateTag"
        />
      </div>
      <ul class="tag-list">
        <li
          v-for="tag in tagStore.tags"
          :key="tag.id"
          class="tag-item"
          :class="{ active: noteStore.filter.tag_id === tag.id }"
          @click="onSelectTag(tag.id)"
        >
          <span class="tag-name"># {{ tag.name }}</span>
          <span class="tag-right">
            <span class="tag-count">{{ tag.note_count }}</span>
            <button class="tag-del" title="删除标签" @click.stop="onDeleteTag(tag)">✕</button>
          </span>
        </li>
        <li v-if="!tagStore.tags.length && !tagCreating" class="empty-hint">暂无标签</li>
      </ul>
    </div>

    <!-- 底部导航 -->
    <div class="sidebar-footer">
      <router-link to="/trash" class="trash-link">🗑 回收站</router-link>
    </div>

    <!-- 分类创建/编辑弹窗 -->
    <CategoryModal
      v-if="modalVisible"
      :category="editingCategory"
      :categories="categoryStore.categories"
      @confirm="onModalConfirm"
      @cancel="modalVisible = false"
    />
  </aside>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import CategoryTree from '@/components/CategoryTree.vue'
import CategoryModal from '@/components/CategoryModal.vue'
import { useNoteStore } from '@/stores/note'
import { useCategoryStore } from '@/stores/category'
import { useTagStore } from '@/stores/tag'
import type { Category, Tag } from '@/types'

defineEmits<{ (e: 'new'): void }>()

const noteStore = useNoteStore()
const categoryStore = useCategoryStore()
const tagStore = useTagStore()

// ==================== 过滤状态计算 ====================
const hasCategoryFilter = computed(() => noteStore.filter.category_id !== undefined)
const hasTagFilter = computed(() => noteStore.filter.tag_id !== undefined)

// ==================== 全部笔记 ====================
function showAllNotes() {
  noteStore.clearFilters()
}

// ==================== 分类操作 ====================
// 弹窗状态
const modalVisible = ref(false)
const editingCategory = ref<Category | null>(null)
// 新建子分类时的父分类 ID
const addSubParentId = ref<number | null>(null)

/** 打开新建分类弹窗 */
function openCreateCategory() {
  editingCategory.value = null
  addSubParentId.value = null
  modalVisible.value = true
}

/** 选中分类（再次点击同一分类则取消） */
function onSelectCategory(id: number) {
  const current = noteStore.filter.category_id
  noteStore.setCategoryFilter(current === id ? undefined : id)
}

/** 重命名分类 */
async function onRenameCategory(id: number, name: string) {
  try {
    await categoryStore.updateCategory(id, { name })
  } catch (err: any) {
    alert(err?.message || '重命名分类失败')
  }
}

/** 删除分类 */
async function onDeleteCategory(cat: Category) {
  if (!confirm(`确定删除分类「${cat.name}」？\n该分类下的笔记将变为未分类，子分类将变为根分类。`)) return
  try {
    await categoryStore.deleteCategory(cat.id)
    // 如果删除的是当前过滤的分类，清除过滤
    if (noteStore.filter.category_id === cat.id) {
      noteStore.clearCategoryFilter()
    }
  } catch (err: any) {
    alert(err?.message || '删除分类失败')
  }
}

/** 新建子分类 — 打开弹窗并预设父分类 */
function onAddSubCategory(parentId: number) {
  editingCategory.value = null
  addSubParentId.value = parentId
  modalVisible.value = true
}

/** 弹窗确认 — 创建或更新分类 */
async function onModalConfirm(data: { name: string; parent_id: number | null }) {
  try {
    if (editingCategory.value) {
      // 编辑模式
      await categoryStore.updateCategory(editingCategory.value.id, {
        name: data.name,
        parent_id: data.parent_id
      })
    } else {
      // 新建模式
      // 如果是通过"新建子分类"触发的，使用预设的父分类 ID
      const parentId = addSubParentId.value !== null ? addSubParentId.value : data.parent_id
      await categoryStore.createCategory({ name: data.name, parent_id: parentId })
    }
    modalVisible.value = false
    editingCategory.value = null
    addSubParentId.value = null
  } catch (err: any) {
    alert(err?.message || '操作失败')
  }
}

// ==================== 标签操作 ====================
const tagCreating = ref(false)
const newTagName = ref('')

/** 打开新建标签输入框 */
function openCreateTag() {
  tagCreating.value = true
  newTagName.value = ''
}

/** 确认创建标签 */
async function confirmCreateTag() {
  const name = newTagName.value.trim()
  if (!name) {
    tagCreating.value = false
    return
  }
  // 检查重名
  if (tagStore.findByName(name)) {
    alert('标签已存在')
    return
  }
  try {
    await tagStore.createTag(name)
  } catch (err: any) {
    alert(err?.message || '创建标签失败')
  }
  tagCreating.value = false
  newTagName.value = ''
}

/** 取消创建标签 */
function cancelCreateTag() {
  tagCreating.value = false
  newTagName.value = ''
}

/** 选中标签（再次点击同一标签则取消） */
function onSelectTag(id: number) {
  const current = noteStore.filter.tag_id
  noteStore.setTagFilter(current === id ? undefined : id)
}

/** 删除标签 */
async function onDeleteTag(tag: Tag) {
  if (!confirm(`确定删除标签「${tag.name}」？`)) return
  try {
    await tagStore.deleteTag(tag.id)
    // 如果删除的是当前过滤的标签，清除过滤
    if (noteStore.filter.tag_id === tag.id) {
      noteStore.clearTagFilter()
    }
  } catch (err: any) {
    alert(err?.message || '删除标签失败')
  }
}
</script>

<style scoped>
.sidebar {
  width: 240px;
  flex-shrink: 0;
  background: #2c3e50;
  color: #ecf0f1;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}
.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid #34495e;
}
.logo {
  font-size: 18px;
  margin-bottom: 12px;
}
.btn-new {
  width: 100%;
  padding: 8px;
  background: #42b983;
  color: #fff;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
}
.btn-new:hover {
  background: #369870;
}
.section {
  padding: 8px 8px;
}
/* 全部笔记按钮 */
.all-notes-btn {
  padding: 8px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: background 0.15s;
}
.all-notes-btn:hover {
  background: #34495e;
}
.all-notes-btn.active {
  background: #42b983;
  color: #fff;
}
/* 区块标题 */
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
  padding: 0 8px;
}
.section-title {
  font-size: 12px;
  color: #95a5a6;
}
.btn-add {
  border: none;
  background: none;
  color: #95a5a6;
  font-size: 16px;
  cursor: pointer;
  padding: 0 4px;
  line-height: 1;
}
.btn-add:hover {
  color: #42b983;
}
/* 标签列表 */
.tag-list {
  list-style: none;
}
.tag-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 8px;
  border-radius: 4px;
  cursor: pointer;
}
.tag-item:hover {
  background: #34495e;
}
.tag-item.active {
  background: #42b983;
}
.tag-name {
  font-size: 14px;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
.tag-right {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}
.tag-count {
  font-size: 12px;
  color: #95a5a6;
  background: #3e556e;
  padding: 1px 6px;
  border-radius: 8px;
  min-width: 18px;
  text-align: center;
}
.tag-item.active .tag-count {
  background: rgba(255, 255, 255, 0.25);
  color: #fff;
}
.tag-del {
  display: none;
  border: none;
  background: none;
  color: #bdc3c7;
  font-size: 11px;
  cursor: pointer;
  padding: 2px;
  line-height: 1;
}
.tag-item:hover .tag-del {
  display: inline;
}
.tag-del:hover {
  color: #e74c3c;
}
/* 新建标签输入框 */
.tag-create-form {
  padding: 0 8px 6px;
}
.tag-input {
  width: 100%;
  padding: 4px 8px;
  border: 1px solid #42b983;
  border-radius: 4px;
  font-size: 13px;
  background: #1a252f;
  color: #fff;
  box-sizing: border-box;
}
.tag-input:focus {
  outline: none;
}
/* 空提示 */
.empty-hint {
  padding: 6px 8px;
  font-size: 13px;
  color: #7f8c8d;
}
/* 底部 */
.sidebar-footer {
  margin-top: auto;
  padding: 12px 16px;
  border-top: 1px solid #34495e;
}
.trash-link {
  font-size: 14px;
  color: #bdc3c7;
  text-decoration: none;
}
.trash-link:hover {
  color: #fff;
}
</style>
