<template>
  <router-view />
</template>

<script setup lang="ts">
// 根组件：仅承载路由出口，全局样式在此声明
</script>

<style>
/* ====== 设计令牌（CSS Custom Properties） ====== */
:root {
  /* 主色 */
  --color-primary: #42b983;
  --color-primary-hover: #369870;
  --color-primary-light: #e8f5e9;
  --color-primary-bg: #f0f7f4;

  /* 语义色 */
  --color-danger: #e74c3c;
  --color-danger-light: #fef0f0;
  --color-warning: #e6a23c;
  --color-warning-light: #fdf6ec;
  --color-success: #67c23a;
  --color-info: #4a90d9;

  /* 中性色 — 严格对比度 */
  --color-text-primary: #1a1a1a;     /* 15.5:1 on white */
  --color-text-secondary: #4a4a4a;   /* 7.5:1 on white */
  --color-text-tertiary: #6b6b6b;    /* 5.0:1 on white */
  --color-text-disabled: #9e9e9e;    /* 2.8:1 — only for disabled */

  /* 侧边栏暗色主题 */
  --color-sidebar-bg: #1e2937;
  --color-sidebar-hover: #334155;
  --color-sidebar-border: #334155;
  --color-sidebar-text: #cbd5e1;
  --color-sidebar-text-muted: #94a3b8;

  /* 背景 */
  --color-bg: #f5f6f7;
  --color-bg-card: #ffffff;
  --color-border: #e2e8f0;
  --color-border-light: #f1f5f9;

  /* 间距（8pt 体系） */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;

  /* 圆角 */
  --radius-sm: 4px;
  --radius-md: 6px;
  --radius-lg: 8px;
  --radius-full: 9999px;

  /* 过渡 */
  --transition-fast: 0.15s ease;
  --transition-base: 0.2s ease;

  /* 阴影 */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.15);

  /* 触控目标最小尺寸 */
  --touch-target: 40px;

  /* 字体 */
  --font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
    'Helvetica Neue', Arial, 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

/* ====== 全局重置 ====== */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html,
body,
#app {
  height: 100%;
  font-family: var(--font-sans);
  color: var(--color-text-primary);
  background: var(--color-bg);
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
}

button {
  cursor: pointer;
  border: none;
  background: none;
  font-size: inherit;
  font-family: inherit;
}

input,
select,
textarea {
  outline: none;
  font-family: inherit;
}

a {
  text-decoration: none;
  color: inherit;
}

/* ====== 可访问性：focus ring ====== */
:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
  border-radius: var(--radius-sm);
}

/* ====== 响应式：移动端适配 ====== */
@media (max-width: 768px) {
  :root {
    --touch-target: 44px;
  }
}

/* ====== 动画：尊重 prefers-reduced-motion ====== */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}

/* ====== 滚动条美化 ====== */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: var(--color-text-disabled);
  border-radius: var(--radius-full);
}
::-webkit-scrollbar-thumb:hover {
  background: var(--color-text-tertiary);
}
</style>
