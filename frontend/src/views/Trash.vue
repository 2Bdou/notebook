<template>
  <div class="trash-page">
    <!-- 顶部标题栏 -->
    <div class="trash-header">
      <router-link to="/" class="back-link">← 返回首页</router-link>
      <h2>🗑 回收站 <span class="trash-count">({{ noteStore.trashTotal }})</span></h2>
      <div class="trash-actions" v-if="noteStore.trashNotes.length">
        <button class="btn-restore-all" @click="restoreAll">全部恢复</button>
        <button class="btn-empty-trash" @click="emptyTrash">清空回收站</button>
      </div>
    </div>

    <!-- 回收站内容 -->
    <div class="trash-body">
      <!-- loading 状态 -->
      <div v-if="noteStore.trashLoading" class="loading-state">加载中...</div>

      <!-- 空状态 -->
      <div v-else-if="!noteStore.trashNotes.length" class="empty-state">
        <div class="empty-icon">🗑</div>
        <p>回收站为空</p>
      </div>

      <!-- 回收站笔记列表 -->
      <template v-else>
        <div
          v-for="note in noteStore.trashNotes"
          :key="note.id"
          class="trash-item"
        >
          <div class="trash-item-info">
            <div class="trash-item-title">{{ note.title || '无标题' }}</div>
            <div class="trash-item-summary">{{ getSummary(note.content) }}</div>
            <div class="trash-item-meta">
              <span class="meta-label">删除时间：</span>
              <span class="meta-date">{{ formatDateTime(note.deleted_at) }}</span>
              <span class="meta-separator">|</span>
              <span class="meta-label">字数：</span>
              <span class="meta-count">{{ note.word_count }}</span>
            </div>
          </div>
          <div class="trash-item-actions">
            <button class="btn-restore" @click="restoreNote(note.id)">恢复</button>
            <button class="btn-force-delete" @click="forceDelete(note)">永久删除</button>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useNoteStore } from '@/stores/note'
import type { Note } from '@/types'

const noteStore = useNoteStore()

// 页面加载时获取回收站笔记
onMounted(() => {
  noteStore.fetchTrashNotes()
})

/** 恢复单条笔记 */
async function restoreNote(id: number) {
  try {
    await noteStore.restoreNote(id)
    // 从回收站列表中移除
    noteStore.trashNotes = noteStore.trashNotes.filter((n) => n.id !== id)
    noteStore.trashTotal--
  } catch (err: any) {
    alert(err?.message || '恢复失败')
  }
}

/** 永久删除单条笔记 */
async function forceDelete(note: Note) {
  if (!confirm(`确定永久删除「${note.title || '无标题'}」？\n此操作不可恢复！`)) return
  try {
    await noteStore.forceDeleteNote(note.id)
    noteStore.trashNotes = noteStore.trashNotes.filter((n) => n.id !== note.id)
    noteStore.trashTotal--
  } catch (err: any) {
    alert(err?.message || '删除失败')
  }
}

/** 批量恢复所有笔记 */
async function restoreAll() {
  if (!confirm(`确定恢复全部 ${noteStore.trashTotal} 条笔记？`)) return
  try {
    const count = await noteStore.restoreAllNotes()
    alert(`已恢复 ${count} 条笔记`)
    await noteStore.fetchTrashNotes()
  } catch (err: any) {
    alert(err?.message || '批量恢复失败')
  }
}

/** 清空回收站 */
async function emptyTrash() {
  if (!confirm('确定清空回收站？\n所有已删除笔记将被永久删除，此操作不可恢复！')) return
  try {
    const count = await noteStore.emptyTrash()
    alert(`已清空 ${count} 条笔记`)
    await noteStore.fetchTrashNotes()
  } catch (err: any) {
    alert(err?.message || '清空回收站失败')
  }
}

/** 提取内容摘要 */
function getSummary(content: string): string {
  const text = content.replace(/[#*`>\-\[\]()!]/g, '').trim()
  return text.slice(0, 100) || '无内容'
}

/** 格式化日期时间 */
function formatDateTime(dateStr: string | null): string {
  if (!dateStr) return '未知'
  const d = new Date(dateStr.replace(' ', 'T'))
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}
</script>

<style scoped>
.trash-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 24px;
}
/* 顶部标题栏 */
.trash-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}
.back-link {
  color: #409eff;
  text-decoration: none;
  font-size: 14px;
}
.back-link:hover {
  text-decoration: underline;
}
.trash-header h2 {
  font-size: 20px;
  flex: 1;
}
.trash-count {
  font-size: 14px;
  color: #999;
  font-weight: normal;
}
.trash-actions {
  display: flex;
  gap: 8px;
}
.btn-restore-all {
  padding: 6px 14px;
  border: 1px solid #42b983;
  border-radius: 4px;
  background: #fff;
  color: #42b983;
  font-size: 13px;
  cursor: pointer;
}
.btn-restore-all:hover {
  background: #e8f5e9;
}
.btn-empty-trash {
  padding: 6px 14px;
  border: 1px solid #f56c6c;
  border-radius: 4px;
  background: #fff;
  color: #f56c6c;
  font-size: 13px;
  cursor: pointer;
}
.btn-empty-trash:hover {
  background: #fef0f0;
}
/* 回收站内容区 */
.trash-body {
  background: #fff;
  border-radius: 8px;
  border: 1px solid #eee;
  overflow: hidden;
}
.loading-state {
  text-align: center;
  color: #999;
  padding: 40px 0;
  font-size: 14px;
}
.empty-state {
  text-align: center;
  color: #999;
  padding: 60px 0;
}
.empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
}
/* 回收站笔记项 */
.trash-item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
  gap: 16px;
}
.trash-item:last-child {
  border-bottom: none;
}
.trash-item:hover {
  background: #fafafa;
}
.trash-item-info {
  flex: 1;
  min-width: 0;
}
.trash-item-title {
  font-size: 15px;
  font-weight: 500;
  margin-bottom: 4px;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
.trash-item-summary {
  font-size: 13px;
  color: #888;
  margin-bottom: 6px;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
.trash-item-meta {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #aaa;
}
.meta-label {
  color: #bbb;
}
.meta-separator {
  color: #ddd;
  margin: 0 4px;
}
/* 操作按钮 */
.trash-item-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}
.btn-restore {
  padding: 5px 12px;
  border: 1px solid #42b983;
  border-radius: 4px;
  background: #fff;
  color: #42b983;
  font-size: 13px;
  cursor: pointer;
  white-space: nowrap;
}
.btn-restore:hover {
  background: #e8f5e9;
}
.btn-force-delete {
  padding: 5px 12px;
  border: 1px solid #f56c6c;
  border-radius: 4px;
  background: #fff;
  color: #f56c6c;
  font-size: 13px;
  cursor: pointer;
  white-space: nowrap;
}
.btn-force-delete:hover {
  background: #fef0f0;
}
</style>
