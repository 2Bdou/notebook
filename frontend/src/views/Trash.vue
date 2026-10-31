<template>
  <div class="trash-page">
    <div class="trash-header">
      <router-link to="/" class="back-link">
        <Icon name="arrow-left" :size="16" />
        <span>返回首页</span>
      </router-link>
      <h2 class="trash-title">
        <Icon name="trash" :size="20" />
        <span>回收站</span>
        <span class="trash-count">({{ noteStore.trashTotal }})</span>
      </h2>
      <div class="trash-actions" v-if="noteStore.trashNotes.length">
        <button class="btn-restore-all" @click="restoreAll">全部恢复</button>
        <button class="btn-empty-trash" @click="emptyTrash">清空回收站</button>
      </div>
    </div>

    <div class="trash-body">
      <div v-if="noteStore.trashLoading" class="loading-state">加载中...</div>
      <div v-else-if="!noteStore.trashNotes.length" class="empty-state">
        <Icon name="trash" :size="48" :stroke-width="1.2" class="empty-icon" />
        <p>回收站为空</p>
      </div>
      <template v-else>
        <div v-for="note in noteStore.trashNotes" :key="note.id" class="trash-item">
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
import Icon from '@/components/Icon.vue'
import { useNoteStore } from '@/stores/note'
import type { Note } from '@/types'

const noteStore = useNoteStore()
onMounted(() => { noteStore.fetchTrashNotes() })

async function restoreNote(id: number) {
  try { await noteStore.restoreNote(id); noteStore.trashNotes = noteStore.trashNotes.filter((n) => n.id !== id); noteStore.trashTotal-- }
  catch (err: any) { alert(err?.message || '恢复失败') }
}
async function forceDelete(note: Note) {
  if (!confirm(`确定永久删除「${note.title || '无标题'}」？\n此操作不可恢复！`)) return
  try { await noteStore.forceDeleteNote(note.id); noteStore.trashNotes = noteStore.trashNotes.filter((n) => n.id !== note.id); noteStore.trashTotal-- }
  catch (err: any) { alert(err?.message || '删除失败') }
}
async function restoreAll() {
  if (!confirm(`确定恢复全部 ${noteStore.trashTotal} 条笔记？`)) return
  try { const count = await noteStore.restoreAllNotes(); alert(`已恢复 ${count} 条笔记`); await noteStore.fetchTrashNotes() }
  catch (err: any) { alert(err?.message || '批量恢复失败') }
}
async function emptyTrash() {
  if (!confirm('确定清空回收站？\n所有已删除笔记将被永久删除，此操作不可恢复！')) return
  try { const count = await noteStore.emptyTrash(); alert(`已清空 ${count} 条笔记`); await noteStore.fetchTrashNotes() }
  catch (err: any) { alert(err?.message || '清空回收站失败') }
}
function getSummary(content: string): string {
  return content.replace(/[#*`>\-\[\]()!]/g, '').trim().slice(0, 100) || '无内容'
}
function formatDateTime(dateStr: string | null): string {
  if (!dateStr) return '未知'
  const d = new Date(dateStr.replace(' ', 'T'))
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}
</script>

<style scoped>
.trash-page { max-width: 800px; margin: 0 auto; padding: var(--space-6); }
.trash-header { display: flex; align-items: center; gap: var(--space-4); margin-bottom: var(--space-6); }
.back-link { display: flex; align-items: center; gap: var(--space-1); color: var(--color-primary); text-decoration: none; font-size: 14px; font-weight: 500; transition: color var(--transition-fast); }
.back-link:hover { color: var(--color-primary-hover); }
.trash-title { font-size: 20px; flex: 1; display: flex; align-items: center; gap: var(--space-2); color: var(--color-text-primary); }
.trash-count { font-size: 14px; color: var(--color-text-tertiary); font-weight: normal; }
.trash-actions { display: flex; gap: var(--space-2); }
.btn-restore-all { padding: 8px 14px; border: 1px solid var(--color-primary); border-radius: var(--radius-md); background: var(--color-bg-card); color: var(--color-primary); font-size: 13px; cursor: pointer; font-weight: 500; transition: all var(--transition-fast); }
.btn-restore-all:hover { background: var(--color-primary-light); }
.btn-empty-trash { padding: 8px 14px; border: 1px solid var(--color-danger); border-radius: var(--radius-md); background: var(--color-bg-card); color: var(--color-danger); font-size: 13px; cursor: pointer; font-weight: 500; transition: all var(--transition-fast); }
.btn-empty-trash:hover { background: var(--color-danger-light); }
.trash-body { background: var(--color-bg-card); border-radius: var(--radius-lg); border: 1px solid var(--color-border); overflow: hidden; }
.loading-state { text-align: center; color: var(--color-text-tertiary); padding: 40px 0; font-size: 14px; }
.empty-state { text-align: center; color: var(--color-text-tertiary); padding: 60px 0; }
.empty-icon { color: var(--color-text-disabled); margin-bottom: var(--space-3); }
.trash-item { display: flex; align-items: flex-start; justify-content: space-between; padding: var(--space-4) var(--space-5); border-bottom: 1px solid var(--color-border-light); gap: var(--space-4); transition: background var(--transition-fast); }
.trash-item:last-child { border-bottom: none; }
.trash-item:hover { background: var(--color-bg); }
.trash-item-info { flex: 1; min-width: 0; }
.trash-item-title { font-size: 15px; font-weight: 500; margin-bottom: 4px; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; color: var(--color-text-primary); }
.trash-item-summary { font-size: 13px; color: var(--color-text-tertiary); margin-bottom: 6px; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
.trash-item-meta { display: flex; align-items: center; gap: 4px; font-size: 12px; color: var(--color-text-tertiary); }
.meta-label { color: var(--color-text-disabled); }
.meta-separator { color: var(--color-border); margin: 0 4px; }
.trash-item-actions { display: flex; gap: var(--space-2); flex-shrink: 0; }
.btn-restore { padding: 6px 12px; border: 1px solid var(--color-primary); border-radius: var(--radius-md); background: var(--color-bg-card); color: var(--color-primary); font-size: 13px; cursor: pointer; white-space: nowrap; font-weight: 500; transition: all var(--transition-fast); }
.btn-restore:hover { background: var(--color-primary-light); }
.btn-force-delete { padding: 6px 12px; border: 1px solid var(--color-danger); border-radius: var(--radius-md); background: var(--color-bg-card); color: var(--color-danger); font-size: 13px; cursor: pointer; white-space: nowrap; font-weight: 500; transition: all var(--transition-fast); }
.btn-force-delete:hover { background: var(--color-danger-light); }
</style>
