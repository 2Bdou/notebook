/**
 * md-editor-v3 全局配置
 * 集成 highlight.js 实现代码语法高亮，避免从 CDN 加载
 */
import hljs from 'highlight.js'
import { config } from 'md-editor-v3'
import type { ToolbarNames } from 'md-editor-v3'

// 配置编辑器扩展：使用本地 highlight.js 实例替代 CDN 加载
config({
  editorExtensions: {
    highlight: {
      instance: hljs
    }
  }
})

/** 排除的工具栏项 */
export const excludedToolbars: ToolbarNames[] = [
  'github',
  'save',
  'pageFullscreen',
  'fullscreen',
  'previewOnly',
  'htmlPreview'
]

/**
 * 统计字数（支持中英文混合）
 * @param text 纯文本内容
 * @returns 字数
 */
export function countWords(text: string): number {
  if (!text) return 0
  // 移除 Markdown 标记符号
  const clean = text
    .replace(/```[\s\S]*?```/g, '') // 代码块
    .replace(/`[^`]*`/g, '') // 行内代码
    .replace(/!\[.*?\]\(.*?\)/g, '') // 图片
    .replace(/\[.*?\]\(.*?\)/g, '$1') // 链接保留文字
    .replace(/[#*~_>|]/g, '') // 标记符号
    .trim()
  // 中文字符数
  const chinese = (clean.match(/[\u4e00-\u9fa5]/g) || []).length
  // 英文单词数
  const english = (clean.replace(/[\u4e00-\u9fa5]/g, ' ').match(/[a-zA-Z0-9]+/g) || []).length
  return chinese + english
}

/**
 * 格式化当前时间为 HH:MM:SS
 */
export function formatTime(): string {
  const now = new Date()
  return [now.getHours(), now.getMinutes(), now.getSeconds()]
    .map((n) => String(n).padStart(2, '0'))
    .join(':')
}
