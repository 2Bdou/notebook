<template>
  <div class="home-layout" :class="{ 'mobile-mode': isMobile }">
    <!-- 桌面端：三栏布局 -->
    <template v-if="!isMobile">
      <Sidebar @new="handleNew" />
      <NoteList @new="handleNew" />
      <NoteEditor />
    </template>

    <!-- 手机端：两面板栈式导航 -->
    <template v-else>
      <!-- 第1层：笔记列表（含折叠的分类/标签） -->
      <div v-show="mobileView === 'list'" class="mobile-panel mobile-list-panel"
        :class="{ 'slide-out-left': mobileView === 'editor', 'slide-in-left': mobileView === 'list' && prevView === 'editor' }">
        <NoteList is-mobile @new="handleNew" @select-note="switchToEditor" />
      </div>
      <!-- 第2层：编辑器 -->
      <div v-show="mobileView === 'editor'" class="mobile-panel mobile-editor-panel"
        :class="{ 'slide-in-right': mobileView === 'editor', 'slide-out-right': mobileView === 'list' }">
        <NoteEditor ref="editorRef" show-back @back="switchToList" />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import Sidebar from '@/components/Sidebar.vue'
import NoteList from '@/components/NoteList.vue'
import NoteEditor from '@/components/NoteEditor.vue'
import { useNoteStore } from '@/stores/note'
import { useCategoryStore } from '@/stores/category'
import { useTagStore } from '@/stores/tag'

const noteStore = useNoteStore()
const categoryStore = useCategoryStore()
const tagStore = useTagStore()

// ====== 响应式：检测手机端 ======
const isMobile = ref(false)
const mobileView = ref<'list' | 'editor'>('list')
const editorRef = ref<InstanceType<typeof NoteEditor> | null>(null)

function checkMobile() {
  isMobile.value = window.innerWidth <= 768
}

// ====== 手机端面板切换 + 返回手势适配 ======
const prevView = ref<'list' | 'editor'>('list')

function switchToEditor() {
  prevView.value = mobileView.value
  mobileView.value = 'editor'
  // 推入一条历史记录，让 iOS 边缘滑动 / Android 返回手势触发 popstate
  history.pushState({ mobileView: 'editor' }, '')
}

/** 返回列表前，先保存未保存的内容（防止 30s 防抖期间丢失） */
function saveBeforeLeave() {
  editorRef.value?.saveImmediately?.()
}

function switchToList() {
  if (mobileView.value === 'list') return
  saveBeforeLeave()
  prevView.value = mobileView.value
  mobileView.value = 'list'
  // 如果是用户点返回按钮触发的，需要回退一条历史记录
  // popstate 会自动处理，这里手动 back 清理
  if (history.state?.mobileView === 'editor') {
    history.back()
  }
}

// 监听 popstate：滑动返回 / 浏览器后退 → 切回列表（不退出应用）
function onPopState() {
  if (mobileView.value === 'editor') {
    saveBeforeLeave()
    prevView.value = 'editor'
    mobileView.value = 'list'
  }
}

// ====== 初始化 ======
onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
  window.addEventListener('popstate', onPopState)
  categoryStore.fetchCategories()
  tagStore.fetchTags()
  noteStore.fetchNotes()
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
  window.removeEventListener('popstate', onPopState)
})

// 新建空白笔记并进入编辑
async function handleNew() {
  const note = await noteStore.createNote({ title: '无标题笔记', content: '' })
  await noteStore.fetchNotes()
  noteStore.current = note
  // 手机端新建后直接跳到编辑器
  if (isMobile.value) {
    switchToEditor()
  }
}
</script>

<style scoped>
.home-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

/* ====== 手机端：单面板全屏 ====== */
.home-layout.mobile-mode {
  flex-direction: column;
}

.mobile-panel {
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.mobile-list-panel {
  display: flex;
}

.mobile-editor-panel {
  display: flex;
}

/* ====== 面板切换动画 (state-transition + navigation-direction) ====== */
.slide-in-right {
  animation: slideInRight 0.25s ease-out;
}
.slide-out-right {
  animation: slideOutRight 0.2s ease-in;
}
.slide-out-left {
  animation: slideOutLeft 0.2s ease-in;
}
.slide-in-left {
  animation: slideInLeft 0.25s ease-out;
}

@keyframes slideInRight {
  from { transform: translateX(100%); opacity: 0.3; }
  to { transform: translateX(0); opacity: 1; }
}
@keyframes slideOutRight {
  from { transform: translateX(0); opacity: 1; }
  to { transform: translateX(100%); opacity: 0.3; }
}
@keyframes slideOutLeft {
  from { transform: translateX(0); opacity: 1; }
  to { transform: translateX(-30%); opacity: 0.3; }
}
@keyframes slideInLeft {
  from { transform: translateX(-30%); opacity: 0.3; }
  to { transform: translateX(0); opacity: 1; }
}

/* Respect prefers-reduced-motion */
@media (prefers-reduced-motion: reduce) {
  .slide-in-right, .slide-out-right, .slide-out-left, .slide-in-left {
    animation: none;
  }
}
</style>
