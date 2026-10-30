/// <reference types="vite/client" />

// 声明 .vue 文件模块，供 TypeScript 识别
declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}
