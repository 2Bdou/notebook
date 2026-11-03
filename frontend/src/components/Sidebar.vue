<template>
  <aside class="sidebar">
    <!-- 顶部标题与新建按钮 -->
    <div class="sidebar-header">
      <div class="logo-row">
        <Icon name="notebook" :size="20" :stroke-width="1.8" class="logo-icon" />
        <h1 class="logo">记事本</h1>
      </div>
      <button class="btn-new" @click="$emit('new')">
        <Icon name="plus" :size="16" />
        <span>新建笔记</span>
      </button>
    </div>

    <!-- 全部笔记按钮 -->
    <div class="section">
      <div
        class="all-notes-btn"
        :class="{ active: !hasCategoryFilter && !hasTagFilter }"
        @click="showAllNotes"
      >
        <Icon name="list" :size="16" />
        <span>全部笔记</span>
      </div>
    </div>

    <!-- 分类区 -->
    <div class="section">
      <div class="section-header">
        <span class="section-title">分类</span>
        <button class="btn-add" title="新建分类" aria-label="新建分类" @click="openCreateCategory">
          <Icon name="plus" :size="14" />
        </button>
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
        <button class="btn-add" title="新建标签" aria-label="新建标签" @click="openCreateTag">
          <Icon name="plus" :size="14" />
        </button>
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
          <Icon name="tag" :size="14" class="tag-icon" />
          <span class="tag-name">{{ tag.name }}</span>
          <span class="tag-right">
            <span class="tag-count">{{ tag.note_count }}</span>
            <button class="tag-del" title="删除标签" aria-label="删除标签" @click.stop="onDeleteTag(tag)">
              <Icon name="x" :size="12" />
            </button>
          </span>
        </li>
        <li v-if="!tagStore.tags.length && !tagCreating" class="empty-hint">暂无标签</li>
      </ul>
    </div>

    <!-- 底部导航 -->
    <div class="sidebar-footer">
      <router-link to="/trash" class="trash-link">
        <Icon name="trash" :size="16" />
        <span>回收站</span>
      </router-link>
      <router-link to="/backup" class="trash-link">
        <Icon name="download" :size="16" />
        <span>备份</span>
      </router-link>
      <div class="user-info" v-if="authStore.user">
        <span class="user-avatar">{{ authStore.user.username.charAt(0).toUpperCase() }}</span>
        <span class="user-name">{{ authStore.user.username }}</span>
        <button class="btn-logout" title="退出登录" aria-label="退出登录" @click="handleLogout">
          <Icon name="logout" :size="16" />
        </button>
      </div>
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
import { useRouter } from 'vue-router'
import Icon from '@/components/Icon.vue'
import CategoryTree from '@/components/CategoryTree.vue'
import CategoryModal from '@/components/CategoryModal.vue'
import { useNoteStore } from '@/stores/note'
import { useCategoryStore } from '@/stores/category'
import { useTagStore } from '@/stores/tag'
import { useAuthStore } from '@/stores/auth'
import type { Category, Tag } from '@/types'

defineEmits<{ (e: 'new'): void }>()

const noteStore = useNoteStore()
const categoryStore = useCategoryStore()
const tagStore = useTagStore()
const authStore = useAuthStore()

const router = useRouter()

/** 退出登录 */
function handleLogout() {
  authStore.logout()
  router.push({ name: 'login' })
}

// ==================== 过滤状态计算 ====================
const hasCategoryFilter = computed(() => noteStore.filter.category_id !== undefined)
const hasTagFilter = computed(() => noteStore.filter.tag_id !== undefined)

// ==================== 全部笔记 ====================
function showAllNotes() {
  noteStore.clearFilters()
}

// ==================== 分类操作 ====================
const modalVisible = ref(false)
const editingCategory = ref<Category | null>(null)
const addSubParentId = ref<number | null>(null)

function openCreateCategory() {
  editingCategory.value = null
  addSubParentId.value = null
  modalVisible.value = true
}

function onSelectCategory(id: number) {
  const current = noteStore.filter.category_id
  noteStore.setCategoryFilter(current === id ? undefined : id)
}

async function onRenameCategory(id: number, name: string) {
  try {
    await categoryStore.updateCategory(id, { name })
  } catch (err: any) {
    alert(err?.message || '重命名分类失败')
  }
}

async function onDeleteCategory(cat: Category) {
  if (!confirm(`确定删除分类「${cat.name}」？\n该分类下的笔记将变为未分类，子分类将变为根分类。`)) return
  try {
    await categoryStore.deleteCategory(cat.id)
    if (noteStore.filter.category_id === cat.id) {
      noteStore.clearCategoryFilter()
    }
  } catch (err: any) {
    alert(err?.message || '删除分类失败')
  }
}

function onAddSubCategory(parentId: number) {
  editingCategory.value = null
  addSubParentId.value = parentId
  modalVisible.value = true
}

async function onModalConfirm(data: { name: string; parent_id: number | null }) {
  try {
    if (editingCategory.value) {
      await categoryStore.updateCategory(editingCategory.value.id, {
        name: data.name,
        parent_id: data.parent_id
      })
    } else {
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

function openCreateTag() {
  tagCreating.value = true
  newTagName.value = ''
}

async function confirmCreateTag() {
  const name = newTagName.value.trim()
  if (!name) {
    tagCreating.value = false
    return
  }
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

function cancelCreateTag() {
  tagCreating.value = false
  newTagName.value = ''
}

function onSelectTag(id: number) {
  const current = noteStore.filter.tag_id
  noteStore.setTagFilter(current === id ? undefined : id)
}

async function onDeleteTag(tag: Tag) {
  if (!confirm(`确定删除标签「${tag.name}」？`)) return
  try {
    await tagStore.deleteTag(tag.id)
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
  background: var(--color-sidebar-bg);
  color: var(--color-sidebar-text);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  transition: width var(--transition-base);
}

.sidebar-header {
  padding: var(--space-4);
  border-bottom: 1px solid var(--color-sidebar-border);
}

.logo-row {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-3);
}

.logo-icon {
  color: var(--color-primary);
}

.logo {
  font-size: 18px;
  font-weight: 600;
  color: #f1f5f9;
}

.btn-new {
  width: 100%;
  padding: 10px;
  background: var(--color-primary);
  color: #fff;
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 500;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  transition: background var(--transition-fast);
  min-height: 40px;
}

.btn-new:hover {
  background: var(--color-primary-hover);
}

.btn-new:active {
  transform: scale(0.98);
}

.section {
  padding: var(--space-2);
}

/* 全部笔记按钮 */
.all-notes-btn {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: 8px 12px;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: background var(--transition-fast);
  min-height: 36px;
}

.all-notes-btn:hover {
  background: var(--color-sidebar-hover);
}

.all-notes-btn.active {
  background: var(--color-primary);
  color: #fff;
}

/* 区块标题 */
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
  padding: 0 var(--space-2);
  min-height: 28px;
}

.section-title {
  font-size: 12px;
  color: var(--color-sidebar-text-muted);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.btn-add {
  color: var(--color-sidebar-text-muted);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
}

.btn-add:hover {
  color: var(--color-primary);
  background: var(--color-sidebar-hover);
}

/* 标签列表 */
.tag-list {
  list-style: none;
}

.tag-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: 6px 8px;
  border-radius: var(--radius-md);
  cursor: pointer;
  min-height: 32px;
  transition: background var(--transition-fast);
}

.tag-item:hover {
  background: var(--color-sidebar-hover);
}

.tag-item.active {
  background: var(--color-primary);
  color: #fff;
}

.tag-icon {
  flex-shrink: 0;
  opacity: 0.7;
}

.tag-item.active .tag-icon {
  opacity: 1;
}

.tag-name {
  font-size: 14px;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  flex: 1;
}

.tag-right {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.tag-count {
  font-size: 12px;
  color: var(--color-sidebar-text-muted);
  background: rgba(255, 255, 255, 0.08);
  padding: 1px 6px;
  border-radius: var(--radius-full);
  min-width: 20px;
  text-align: center;
}

.tag-item.active .tag-count {
  background: rgba(255, 255, 255, 0.25);
  color: #fff;
}

.tag-del {
  display: none;
  color: var(--color-sidebar-text);
  cursor: pointer;
  padding: 4px;
  border-radius: var(--radius-sm);
  line-height: 1;
  transition: color var(--transition-fast);
}

.tag-item:hover .tag-del {
  display: inline-flex;
}

.tag-del:hover {
  color: var(--color-danger);
  background: rgba(231, 76, 60, 0.15);
}

/* 新建标签输入框 */
.tag-create-form {
  padding: 0 var(--space-2) 6px;
}

.tag-input {
  width: 100%;
  padding: 6px 8px;
  border: 1px solid var(--color-primary);
  border-radius: var(--radius-md);
  font-size: 13px;
  background: #0f172a;
  color: #fff;
  box-sizing: border-box;
}

.tag-input:focus {
  outline: none;
  box-shadow: 0 0 0 3px rgba(66, 185, 131, 0.15);
}

/* 空提示 */
.empty-hint {
  padding: 6px 8px;
  font-size: 13px;
  color: var(--color-sidebar-text-muted);
}

/* 底部 */
.sidebar-footer {
  margin-top: auto;
  padding: var(--space-3) var(--space-4);
  border-top: 1px solid var(--color-sidebar-border);
}

.trash-link {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: 14px;
  color: var(--color-sidebar-text);
  padding: 6px 0;
  min-height: 32px;
  transition: color var(--transition-fast);
}

.trash-link:hover {
  color: #f1f5f9;
}

/* 用户信息区 */
.user-info {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-top: var(--space-3);
  padding-top: var(--space-3);
  border-top: 1px solid var(--color-sidebar-border);
}

.user-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--color-primary);
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.user-name {
  font-size: 14px;
  color: #e2e8f0;
  flex: 1;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.btn-logout {
  color: var(--color-sidebar-text-muted);
  padding: 6px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-fast);
}

.btn-logout:hover {
  color: var(--color-danger);
  background: rgba(231, 76, 60, 0.1);
}

/* 响应式：移动端侧边栏 */
@media (max-width: 768px) {
  .sidebar {
    width: 200px;
  }
}
</style>
