<template>
  <div class="note-editor" @keydown="handleKeydown" @paste="handlePaste">
    <!-- 空状态 -->
    <div v-if="!noteStore.current" class="empty-editor">
      <div class="empty-icon">📝</div>
      <p>选择或新建一篇笔记开始编辑</p>
    </div>

    <!-- 编辑区 -->
    <template v-else>
      <!-- 顶部标题栏 -->
      <div class="editor-header">
        <input
          v-model="title"
          class="title-input"
          placeholder="笔记标题"
          @input="onContentChange"
        />
        <div class="editor-actions">
          <!-- 编辑模式切换：编辑 / 双栏 / 预览 -->
          <div class="mode-switcher">
            <button
              class="mode-btn"
              :class="{ active: editMode === 'edit' }"
              title="编辑模式"
              @click="setEditMode('edit')"
            >✏️</button>
            <button
              class="mode-btn"
              :class="{ active: editMode === 'dual' }"
              title="双栏模式"
              @click="setEditMode('dual')"
            >📖</button>
            <button
              class="mode-btn"
              :class="{ active: editMode === 'preview' }"
              title="预览模式"
              @click="setEditMode('preview')"
            >👁️</button>
          </div>
          <button
            class="btn-pin"
            :class="{ pinned: noteStore.current.is_pinned }"
            @click="togglePin"
          >
            {{ noteStore.current.is_pinned ? '📌 已置顶' : '置顶' }}
          </button>
          <button class="btn-delete" @click="deleteNote">删除</button>
        </div>
      </div>

      <!-- 标签关联区域 -->
      <div class="tag-bar">
        <div class="tag-bar-left">
          <span class="tag-bar-label">标签：</span>
          <!-- 已关联的标签（点击 ✕ 移除） -->
          <span
            v-for="tag in currentTags"
            :key="tag.id"
            class="tag-chip"
          >
            {{ tag.name }}
            <button class="tag-remove" @click="removeTag(tag.id)">✕</button>
          </span>
          <!-- 无标签提示 -->
          <span v-if="!currentTags.length" class="no-tags-hint">暂无标签</span>
        </div>
        <div class="tag-bar-right">
          <!-- 添加标签按钮 -->
          <button class="btn-add-tag" @click="showTagDropdown = !showTagDropdown">
            + 添加标签
          </button>
          <!-- 标签选择下拉 -->
          <div v-if="showTagDropdown" class="tag-dropdown" @click.stop>
            <!-- 新建标签输入 -->
            <div class="tag-new-row">
              <input
                v-model="newTagName"
                class="tag-new-input"
                placeholder="输入新标签名称..."
                maxlength="20"
                @keydown.enter="createAndAddTag"
              />
              <button
                class="tag-new-btn"
                :disabled="!newTagName.trim()"
                @click="createAndAddTag"
              >新建并添加</button>
            </div>
            <!-- 已有标签列表（排除已关联的） -->
            <div class="tag-dropdown-list">
              <div
                v-for="tag in availableTags"
                :key="tag.id"
                class="tag-dropdown-item"
                @click="addTag(tag.id, tag.name)"
              >
                <span># {{ tag.name }}</span>
                <span class="tag-dropdown-count">{{ tag.note_count }}</span>
              </div>
              <div v-if="!availableTags.length" class="tag-dropdown-empty">
                无可用标签，请新建
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 编辑器主体 -->
      <div class="editor-body">
        <MdEditor
          ref="editorRef"
          v-model="content"
          :theme="editorTheme"
          :preview="showPreview"
          :toolbars-exclude="excludedToolbars"
          :on-save="handleEditorSave"
          :on-html-changed="handleHtmlChanged"
          :on-get-catalog="handleGetCatalog"
          preview-theme="default"
          code-theme="atom"
          catalog-layout="flat"
          :catalog-max-depth="6"
          language="zh-CN"
          :footers="[]"
          style="height: 100%"
        />
      </div>

      <!-- 底部状态栏：字数统计 + 保存状态 -->
      <div class="editor-footer">
        <span class="footer-left">
          <span class="word-count">📄 {{ wordCount }} 字</span>
          <span class="separator">|</span>
          <span class="mode-label">{{ modeLabel }}</span>
        </span>
        <span class="footer-right">
          <span class="save-status" :class="saveStatusClass">
            {{ saveStatusText }}
          </span>
        </span>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { MdEditor } from 'md-editor-v3'
import 'md-editor-v3/lib/style.css'
import { useNoteStore } from '@/stores/note'
import { useTagStore } from '@/stores/tag'
// 导入 md-editor 全局配置（执行 highlight.js 集成）及工具函数
import { excludedToolbars, countWords, formatTime } from '@/utils/md-config'
import type { NoteTag } from '@/types'

const noteStore = useNoteStore()
const tagStore = useTagStore()

// ==================== 响应式状态 ====================
const title = ref('')
const content = ref('')
const htmlContent = ref('') // 编辑器渲染后的 HTML
const editorRef = ref<any>(null) // MdEditor 组件引用

// 编辑模式：edit（仅编辑）/ dual（双栏）/ preview（仅预览）
type EditMode = 'edit' | 'preview' | 'dual'
const editMode = ref<EditMode>('dual')

// 保存状态：saved（已保存）/ saving（保存中）/ unsaved（未保存）/ error（保存失败）
type SaveStatus = 'saved' | 'saving' | 'unsaved' | 'error'
const saveStatus = ref<SaveStatus>('saved')
const savedTime = ref('') // 上次保存成功时间
const errorMsg = ref('') // 保存失败错误信息

// ==================== 主题跟随系统暗色/亮色模式 ====================
const isDark = ref(false)
let mediaQuery: MediaQueryList | null = null

function initTheme() {
  mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
  isDark.value = mediaQuery.matches
  mediaQuery.addEventListener('change', (e) => {
    isDark.value = e.matches
  })
}

// 编辑器主题：light / dark
const editorTheme = computed<'light' | 'dark'>(() => (isDark.value ? 'dark' : 'light'))

// ==================== 编辑模式切换 ====================
const showPreview = computed(() => editMode.value === 'dual')
const modeLabel = computed(() => {
  const labels: Record<EditMode, string> = {
    edit: '编辑模式',
    dual: '双栏模式',
    preview: '预览模式'
  }
  return labels[editMode.value]
})

function setEditMode(mode: EditMode) {
  editMode.value = mode
}

// 监听模式变化，通过暴露的 API 切换 previewOnly
watch(editMode, (mode) => {
  nextTick(() => {
    const editor = editorRef.value
    if (!editor) return
    if (mode === 'preview') {
      editor.togglePreviewOnly(true)
    } else {
      editor.togglePreviewOnly(false)
    }
  })
})

// ==================== 字数统计 ====================
const wordCount = computed(() => countWords(content.value))

// ==================== 目录预览 ====================
function handleGetCatalog(_list: any[]) {
  // 目录数据由编辑器内部渲染，此处仅做占位
}

// ==================== HTML 内容同步 ====================
function handleHtmlChanged(html: string) {
  htmlContent.value = html
}

// ==================== 图片粘贴支持 ====================
function handlePaste(e: ClipboardEvent) {
  const items = e.clipboardData?.items
  if (!items) return
  for (const item of items) {
    if (item.type.startsWith('image/')) {
      e.preventDefault()
      const file = item.getAsFile()
      if (!file) continue
      const reader = new FileReader()
      reader.onload = () => {
        const base64 = reader.result as string
        const imgMarkdown = `\n![](${base64})\n`
        // 优先使用编辑器 insert 方法在光标处插入
        const editor = editorRef.value
        if (editor?.insert) {
          editor.insert(() => ({ targetValue: imgMarkdown }))
        } else {
          // 降级：追加到末尾
          content.value += imgMarkdown
        }
      }
      reader.readAsDataURL(file)
    }
  }
}

// ==================== 自动保存（防抖 2 秒） ====================
let saveTimer: ReturnType<typeof setTimeout> | null = null

/** 标记内容已修改，启动防抖保存 */
function onContentChange() {
  if (!noteStore.current) return
  saveStatus.value = 'unsaved'
  if (saveTimer) clearTimeout(saveTimer)
  saveTimer = setTimeout(() => {
    doSave()
  }, 2000)
}

/** 执行保存请求 */
async function doSave() {
  if (!noteStore.current) return
  saveStatus.value = 'saving'
  try {
    const id = noteStore.current.id
    await noteStore.updateNote(id, {
      title: title.value,
      content: content.value,
      content_html: htmlContent.value
    })
    // 静默刷新列表以同步标题与摘要
    await noteStore.fetchNotes()
    saveStatus.value = 'saved'
    savedTime.value = formatTime()
    errorMsg.value = ''
  } catch (err: any) {
    saveStatus.value = 'error'
    errorMsg.value = err?.message || '未知错误'
  }
}

/** 立即保存（Ctrl+S 触发，跳过防抖等待） */
function saveImmediately() {
  if (!noteStore.current) return
  if (saveTimer) {
    clearTimeout(saveTimer)
    saveTimer = null
  }
  doSave()
}

// ==================== 编辑器内置保存事件 ====================
function handleEditorSave(_v: string, _h: Promise<string>) {
  saveImmediately()
}

// ==================== 快捷键：Ctrl+S 手动保存 ====================
function handleKeydown(e: KeyboardEvent) {
  if ((e.ctrlKey || e.metaKey) && e.key === 's') {
    e.preventDefault()
    saveImmediately()
  }
  // 点击标签下拉外部时关闭
  if (e.key === 'Escape' && showTagDropdown.value) {
    showTagDropdown.value = false
  }
}

// ==================== 保存状态显示 ====================
const saveStatusClass = computed(() => ({
  'status-saved': saveStatus.value === 'saved',
  'status-saving': saveStatus.value === 'saving',
  'status-unsaved': saveStatus.value === 'unsaved',
  'status-error': saveStatus.value === 'error'
}))

const saveStatusText = computed(() => {
  switch (saveStatus.value) {
    case 'saved':
      return savedTime.value ? `✅ 已保存 ${savedTime.value}` : '✅ 已保存'
    case 'saving':
      return '⏳ 保存中...'
    case 'unsaved':
      return '✏️ 编辑中...'
    case 'error':
      return `❌ 保存失败: ${errorMsg.value}`
    default:
      return ''
  }
})

// ==================== 标签关联 ====================
const showTagDropdown = ref(false)
const newTagName = ref('')

/** 当前笔记的标签列表 */
const currentTags = computed<NoteTag[]>(() => noteStore.current?.tags || [])

/** 可添加的标签列表（排除已关联的） */
const availableTags = computed(() => {
  const currentIds = new Set(currentTags.value.map((t) => t.id))
  return tagStore.tags.filter((t) => !currentIds.has(t.id))
})

/** 添加已有标签到当前笔记 */
async function addTag(tagId: number, tagName: string) {
  if (!noteStore.current) return
  const tagIds = [...currentTags.value.map((t) => t.id), tagId]
  try {
    await noteStore.updateNoteTags(noteStore.current.id, tagIds)
    // 更新当前笔记的标签（本地同步）
    noteStore.current.tags = [...currentTags.value, { id: tagId, name: tagName }]
    // 刷新标签列表（更新笔记计数）和笔记列表
    await tagStore.fetchTags()
    await noteStore.fetchNotes()
  } catch (err: any) {
    alert(err?.message || '添加标签失败')
  }
}

/** 移除标签 */
async function removeTag(tagId: number) {
  if (!noteStore.current) return
  const tagIds = currentTags.value.filter((t) => t.id !== tagId).map((t) => t.id)
  try {
    await noteStore.updateNoteTags(noteStore.current.id, tagIds)
    // 更新当前笔记的标签
    noteStore.current.tags = currentTags.value.filter((t) => t.id !== tagId)
    await tagStore.fetchTags()
    await noteStore.fetchNotes()
  } catch (err: any) {
    alert(err?.message || '移除标签失败')
  }
}

/** 新建标签并添加到当前笔记 */
async function createAndAddTag() {
  const name = newTagName.value.trim()
  if (!name || !noteStore.current) return
  // 检查重名
  const existing = tagStore.findByName(name)
  if (existing) {
    // 标签已存在，直接添加
    await addTag(existing.id, existing.name)
    newTagName.value = ''
    return
  }
  try {
    const tag = await tagStore.createTag(name)
    await addTag(tag.id, tag.name)
    newTagName.value = ''
  } catch (err: any) {
    alert(err?.message || '创建标签失败')
  }
}

// ==================== 笔记切换同步 ====================
watch(
  () => noteStore.current,
  (note) => {
    if (note) {
      title.value = note.title
      content.value = note.content
      saveStatus.value = 'saved'
      savedTime.value = ''
      errorMsg.value = ''
      // 切换笔记时关闭标签下拉
      showTagDropdown.value = false
      newTagName.value = ''
    }
  }
)

// 内容变化时触发防抖保存
watch([title, content], () => {
  onContentChange()
})

// ==================== 置顶 / 删除 ====================
async function togglePin() {
  if (!noteStore.current) return
  const pinned = !noteStore.current.is_pinned
  // 即时更新 UI 状态（不用等保存完成）
  noteStore.current.is_pinned = pinned
  try {
    await noteStore.updateNote(noteStore.current.id, { is_pinned: pinned })
    // 同步列表中对应笔记的置顶状态并重新加载（置顶笔记移到最前）
    const target = noteStore.notes.find((n) => n.id === noteStore.current!.id)
    if (target) target.is_pinned = pinned
    await noteStore.fetchNotes()
  } catch (err: any) {
    // 失败时回滚状态
    noteStore.current.is_pinned = !pinned
    alert(err?.message || '置顶操作失败')
  }
}

async function deleteNote() {
  if (!noteStore.current) return
  if (!confirm('确定删除该笔记？')) return
  try {
    await noteStore.deleteNote(noteStore.current.id)
    noteStore.current = null
    await noteStore.fetchNotes()
  } catch (err: any) {
    alert(err?.message || '删除失败')
  }
}

// ==================== 全局点击关闭标签下拉 ====================
function onGlobalClick(e: MouseEvent) {
  if (showTagDropdown.value) {
    const target = e.target as HTMLElement
    if (!target.closest('.tag-bar-right')) {
      showTagDropdown.value = false
    }
  }
}

// ==================== 生命周期 ====================
onMounted(() => {
  initTheme()
  document.addEventListener('click', onGlobalClick)
})

onUnmounted(() => {
  if (saveTimer) clearTimeout(saveTimer)
  if (mediaQuery) {
    mediaQuery.removeEventListener('change', () => {})
  }
  document.removeEventListener('click', onGlobalClick)
})
</script>

<style scoped>
.note-editor {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #fff;
}
.empty-editor {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #999;
}
.empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
}
.editor-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  border-bottom: 1px solid #eee;
}
.title-input {
  flex: 1;
  font-size: 18px;
  font-weight: 500;
  border: none;
  padding: 4px 0;
  background: transparent;
}
.title-input:focus {
  border-bottom: 1px solid #42b983;
  outline: none;
}
.editor-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
/* 编辑模式切换按钮组 */
.mode-switcher {
  display: flex;
  gap: 2px;
  padding: 2px;
  border-radius: 6px;
  background: #f5f5f5;
}
.mode-btn {
  padding: 4px 8px;
  border: none;
  border-radius: 4px;
  background: transparent;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.2s;
}
.mode-btn:hover {
  background: #e0e0e0;
}
.mode-btn.active {
  background: #42b983;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.15);
}
.btn-pin,
.btn-delete {
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 13px;
  border: 1px solid #ddd;
  background: #fff;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-pin:hover {
  border-color: #e6a23c;
  color: #e6a23c;
}
.btn-pin.pinned {
  background: #fdf6ec;
  border-color: #e6a23c;
  color: #e6a23c;
}
.btn-delete:hover {
  border-color: #f56c6c;
  color: #f56c6c;
}
/* 标签关联区域 */
.tag-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 20px;
  border-bottom: 1px solid #eee;
  background: #fafafa;
  min-height: 36px;
}
.tag-bar-left {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
  flex-wrap: wrap;
}
.tag-bar-label {
  font-size: 13px;
  color: #999;
  flex-shrink: 0;
}
/* 已关联标签芯片 */
.tag-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  background: #e8f5e9;
  color: #42b983;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 500;
}
.tag-remove {
  border: none;
  background: none;
  cursor: pointer;
  font-size: 10px;
  color: #42b983;
  padding: 0;
  line-height: 1;
  opacity: 0.5;
}
.tag-remove:hover {
  opacity: 1;
  color: #f56c6c;
}
.no-tags-hint {
  font-size: 12px;
  color: #ccc;
}
/* 添加标签按钮 + 下拉 */
.tag-bar-right {
  position: relative;
  flex-shrink: 0;
}
.btn-add-tag {
  padding: 4px 10px;
  border: 1px dashed #42b983;
  border-radius: 4px;
  background: transparent;
  color: #42b983;
  font-size: 12px;
  cursor: pointer;
}
.btn-add-tag:hover {
  background: #e8f5e9;
}
/* 标签下拉面板 */
.tag-dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 4px;
  width: 240px;
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 6px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  z-index: 100;
  overflow: hidden;
}
/* 新建标签行 */
.tag-new-row {
  display: flex;
  gap: 6px;
  padding: 8px;
  border-bottom: 1px solid #eee;
}
.tag-new-input {
  flex: 1;
  padding: 4px 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 13px;
  min-width: 0;
}
.tag-new-input:focus {
  border-color: #42b983;
  outline: none;
}
.tag-new-btn {
  padding: 4px 8px;
  border: none;
  border-radius: 4px;
  background: #42b983;
  color: #fff;
  font-size: 12px;
  cursor: pointer;
  white-space: nowrap;
}
.tag-new-btn:disabled {
  background: #a5d6b8;
  cursor: not-allowed;
}
/* 标签列表 */
.tag-dropdown-list {
  max-height: 200px;
  overflow-y: auto;
}
.tag-dropdown-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 12px;
  font-size: 13px;
  cursor: pointer;
}
.tag-dropdown-item:hover {
  background: #f0f7f4;
}
.tag-dropdown-count {
  font-size: 11px;
  color: #bbb;
}
.tag-dropdown-empty {
  padding: 12px;
  font-size: 13px;
  color: #ccc;
  text-align: center;
}
.editor-body {
  flex: 1;
  overflow: hidden;
}
/* 底部状态栏 */
.editor-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 20px;
  border-top: 1px solid #eee;
  font-size: 12px;
  color: #999;
  background: #fafafa;
}
.footer-left {
  display: flex;
  align-items: center;
  gap: 8px;
}
.separator {
  color: #ddd;
}
.mode-label {
  color: #bbb;
}
.footer-right {
  display: flex;
  align-items: center;
}
/* 保存状态样式 */
.save-status {
  font-weight: 500;
}
.status-saved {
  color: #67c23a;
}
.status-saving {
  color: #e6a23c;
}
.status-unsaved {
  color: #909399;
}
.status-error {
  color: #f56c6c;
}

/* 暗色模式适配 */
:global(.dark) .note-editor,
:global([data-theme='dark']) .note-editor {
  background: #1e1e1e;
}
</style>
