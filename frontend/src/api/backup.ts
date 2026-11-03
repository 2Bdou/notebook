import axios from 'axios'
import { http } from './request'

/** 导出备份：触发浏览器下载 JSON 文件 */
export async function exportBackup(): Promise<void> {
  const token = localStorage.getItem('token')
  const response = await axios.get('/api/backup/export', {
    responseType: 'blob',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  // 从 Content-Disposition 提取文件名
  const disposition = response.headers['content-disposition'] || ''
  const match = disposition.match(/filename="?(.+?)"?$/)
  const filename = match?.[1] || `notebook-backup-${Date.now()}.json`

  // 创建下载链接
  const blob = new Blob([response.data], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

/** 导入备份：上传 JSON 文件 */
export async function importBackup(file: File): Promise<{
  categories: number
  tags: number
  notes: number
}> {
  const formData = new FormData()
  formData.append('file', file)
  return http.post('/backup/import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
