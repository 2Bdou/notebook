<template>
  <div class="backup-page">
    <div class="backup-header">
      <router-link to="/" class="back-link">
        <Icon name="arrow-left" :size="16" />
        <span>返回首页</span>
      </router-link>
      <h2 class="backup-title">
        <Icon name="download" :size="20" />
        <span>备份管理</span>
      </h2>
    </div>

    <div class="backup-body">
      <!-- 导出区域 -->
      <div class="backup-card">
        <div class="card-icon">
          <Icon name="download" :size="24" />
        </div>
        <div class="card-content">
          <h3 class="card-title">导出备份</h3>
          <p class="card-desc">将你的全部笔记、分类和标签导出为 JSON 文件，保存到本地。</p>
        </div>
        <button class="btn-primary" :disabled="exporting" @click="handleExport">
          <Icon v-if="exporting" name="loader" :size="16" class="spin" />
          <Icon v-else name="download" :size="16" />
          <span>{{ exporting ? '导出中...' : '导出' }}</span>
        </button>
      </div>

      <!-- 导入区域 -->
      <div class="backup-card">
        <div class="card-icon">
          <Icon name="upload" :size="24" />
        </div>
        <div class="card-content">
          <h3 class="card-title">导入备份</h3>
          <p class="card-desc">从 JSON 文件导入数据。分类和标签按名称合并，笔记全部新增。</p>
        </div>
        <button class="btn-secondary" :disabled="importing" @click="triggerImport">
          <Icon v-if="importing" name="loader" :size="16" class="spin" />
          <Icon v-else name="upload" :size="16" />
          <span>{{ importing ? '导入中...' : '选择文件' }}</span>
        </button>
        <input ref="fileInputRef" type="file" accept=".json,application/json" class="file-input" @change="handleImport" />
      </div>

      <!-- 导入结果 -->
      <div v-if="importResult" class="result-card">
        <div class="result-icon">
          <Icon name="check" :size="20" />
        </div>
        <div class="result-content">
          <h3 class="result-title">导入完成</h3>
          <p class="result-detail">
            新增分类 {{ importResult.categories }} 个 ·
            新增标签 {{ importResult.tags }} 个 ·
            导入笔记 {{ importResult.notes }} 篇
          </p>
        </div>
        <button class="btn-text" @click="importResult = null">关闭</button>
      </div>

      <!-- 错误提示 -->
      <div v-if="errorMsg" class="error-card">
        <div class="error-icon">
          <Icon name="x" :size="20" />
        </div>
        <div class="error-content">
          <h3 class="error-title">操作失败</h3>
          <p class="error-detail">{{ errorMsg }}</p>
        </div>
        <button class="btn-text" @click="errorMsg = ''">关闭</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import Icon from '@/components/Icon.vue'
import { exportBackup, importBackup } from '@/api/backup'
import { useNoteStore } from '@/stores/note'
import { useCategoryStore } from '@/stores/category'
import { useTagStore } from '@/stores/tag'

const router = useRouter()
const noteStore = useNoteStore()
const categoryStore = useCategoryStore()
const tagStore = useTagStore()

const exporting = ref(false)
const importing = ref(false)
const importResult = ref<{ categories: number; tags: number; notes: number } | null>(null)
const errorMsg = ref('')
const fileInputRef = ref<HTMLInputElement | null>(null)

async function handleExport() {
  exporting.value = true
  errorMsg.value = ''
  try {
    await exportBackup()
  } catch (err: any) {
    errorMsg.value = err?.message || '导出失败'
  } finally {
    exporting.value = false
  }
}

function triggerImport() {
  fileInputRef.value?.click()
}

async function handleImport(e: Event) {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  importing.value = true
  errorMsg.value = ''
  importResult.value = null
  try {
    const result = await importBackup(file)
    importResult.value = result
    // 刷新前端数据
    await Promise.all([
      noteStore.fetchNotes(),
      categoryStore.fetchCategories(),
      tagStore.fetchTags(),
    ])
  } catch (err: any) {
    errorMsg.value = err?.message || '导入失败'
  } finally {
    importing.value = false
    target.value = '' // 清空 input 以便重复选同一文件
  }
}
</script>

<style scoped>
.backup-page { max-width: 800px; margin: 0 auto; padding: var(--space-6); }

/* 头部 */
.backup-header { display: flex; align-items: center; gap: var(--space-4); margin-bottom: var(--space-6); }
.back-link { display: flex; align-items: center; gap: var(--space-1); color: var(--color-primary); text-decoration: none; font-size: 14px; font-weight: 500; transition: color var(--transition-fast); min-height: 44px; }
.back-link:hover { color: var(--color-primary-hover); }
.back-link:focus-visible { outline: 2px solid var(--color-primary); outline-offset: 2px; }
.backup-title { font-size: 20px; flex: 1; display: flex; align-items: center; gap: var(--space-2); color: var(--color-text-primary); }

/* 卡片 */
.backup-body { display: flex; flex-direction: column; gap: var(--space-4); }
.backup-card { display: flex; align-items: center; gap: var(--space-4); padding: var(--space-5); background: var(--color-bg-card); border-radius: var(--radius-lg); border: 1px solid var(--color-border); }
.card-icon { width: 48px; height: 48px; border-radius: var(--radius-md); background: var(--color-primary-bg); display: flex; align-items: center; justify-content: center; color: var(--color-primary); flex-shrink: 0; }
.card-content { flex: 1; min-width: 0; }
.card-title { font-size: 16px; font-weight: 600; color: var(--color-text-primary); margin-bottom: 4px; }
.card-desc { font-size: 13px; color: var(--color-text-tertiary); line-height: 1.5; }

/* 按钮 */
.btn-primary { display: flex; align-items: center; gap: 6px; padding: 10px 18px; border: none; border-radius: var(--radius-md); background: var(--color-primary); color: #fff; font-size: 14px; font-weight: 500; cursor: pointer; min-height: 44px; transition: all var(--transition-fast); flex-shrink: 0; }
.btn-primary:hover:not(:disabled) { background: var(--color-primary-hover); }
.btn-primary:active:not(:disabled) { transform: scale(0.96); }
.btn-primary:focus-visible { outline: 2px solid var(--color-primary); outline-offset: 2px; }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }

.btn-secondary { display: flex; align-items: center; gap: 6px; padding: 10px 18px; border: 1px solid var(--color-primary); border-radius: var(--radius-md); background: var(--color-bg-card); color: var(--color-primary); font-size: 14px; font-weight: 500; cursor: pointer; min-height: 44px; transition: all var(--transition-fast); flex-shrink: 0; }
.btn-secondary:hover:not(:disabled) { background: var(--color-primary-light); }
.btn-secondary:active:not(:disabled) { transform: scale(0.96); }
.btn-secondary:focus-visible { outline: 2px solid var(--color-primary); outline-offset: 2px; }
.btn-secondary:disabled { opacity: 0.6; cursor: not-allowed; }

.btn-text { padding: 8px 12px; border: none; background: transparent; color: var(--color-text-tertiary); font-size: 13px; cursor: pointer; min-height: 44px; border-radius: var(--radius-md); }
.btn-text:hover { color: var(--color-text-primary); background: var(--color-bg); }
.btn-text:focus-visible { outline: 2px solid var(--color-primary); outline-offset: 2px; }
.btn-text:active { transform: scale(0.96); }

.file-input { display: none; }

/* 结果卡片 */
.result-card { display: flex; align-items: center; gap: var(--space-4); padding: var(--space-4) var(--space-5); background: var(--color-success-light); border-radius: var(--radius-lg); border: 1px solid var(--color-success); }
.result-icon { width: 40px; height: 40px; border-radius: 50%; background: var(--color-success); color: #fff; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.result-content { flex: 1; }
.result-title { font-size: 15px; font-weight: 600; color: var(--color-text-primary); margin-bottom: 2px; }
.result-detail { font-size: 13px; color: var(--color-text-secondary); }

/* 错误卡片 */
.error-card { display: flex; align-items: center; gap: var(--space-4); padding: var(--space-4) var(--space-5); background: var(--color-danger-light); border-radius: var(--radius-lg); border: 1px solid var(--color-danger); }
.error-icon { width: 40px; height: 40px; border-radius: 50%; background: var(--color-danger); color: #fff; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.error-content { flex: 1; }
.error-title { font-size: 15px; font-weight: 600; color: var(--color-text-primary); margin-bottom: 2px; }
.error-detail { font-size: 13px; color: var(--color-text-secondary); }

/* 触摸优化 */
.btn-primary, .btn-secondary, .btn-text, .back-link { touch-action: manipulation; }

/* 动画 */
.spin { animation: spin 0.8s linear infinite; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
@media (prefers-reduced-motion: reduce) { .spin { animation: none; } }
</style>
