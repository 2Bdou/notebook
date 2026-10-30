<template>
  <div class="home-layout">
    <Sidebar @new="handleNew" />
    <NoteList />
    <NoteEditor />
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import Sidebar from '@/components/Sidebar.vue'
import NoteList from '@/components/NoteList.vue'
import NoteEditor from '@/components/NoteEditor.vue'
import { useNoteStore } from '@/stores/note'
import { useCategoryStore } from '@/stores/category'
import { useTagStore } from '@/stores/tag'

const noteStore = useNoteStore()
const categoryStore = useCategoryStore()
const tagStore = useTagStore()

// 初始化加载分类、标签、笔记列表
onMounted(() => {
  categoryStore.fetchCategories()
  tagStore.fetchTags()
  noteStore.fetchNotes()
})

// 新建空白笔记并进入编辑
async function handleNew() {
  const note = await noteStore.createNote({ title: '无标题笔记', content: '' })
  await noteStore.fetchNotes()
  noteStore.current = note
}
</script>

<style scoped>
.home-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
}
</style>
