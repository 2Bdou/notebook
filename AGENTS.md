# AGENTS.md — Notebook 项目维护指南

> 本文件供后续接手的 AI agent 或人类开发者阅读。包含项目架构、已固化的原则、技术栈和开发约定。

## 项目概述

Markdown 笔记本应用，支持多用户、分类、标签、全文搜索、回收站、备份导入导出。
前后端分离，Docker Compose 一键部署。

- **仓库**：GitHub `2Bdou/notebook` + GitCode `realdou/notebook`（双远程同步）
- **部署**：`docker-compose up -d`，前端监听 `127.0.0.1:8080`（nginx 反代）

## 技术栈

| 层 | 技术 | 说明 |
|---|---|---|
| 后端 | FastAPI + aiosqlite | 异步 Python，SQLite 单文件数据库 |
| 前端 | Vue 3 + TypeScript + Pinia + Vue Router | Vite 构建，MdEditor v3 编辑器 |
| 认证 | JWT (python-jose) + bcrypt | 无状态认证，多用户数据隔离 |
| 部署 | Docker Compose | 前端 nginx 静态托管 + 反代后端 API |

## 目录结构

```
notebook/
├── backend/
│   ├── main.py              # FastAPI 入口，挂载所有路由
│   ├── config.py            # 环境变量配置
│   ├── database.py          # SQLite 建表 + 迁移
│   ├── deps.py              # 认证依赖 + 速率限制
│   ├── models/              # 数据模型（user, note, category, tag）
│   ├── schemas/             # Pydantic 请求/响应 schema
│   └── routers/             # API 路由
│       ├── auth.py          # 注册/登录/当前用户
│       ├── notes.py         # 笔记 CRUD + 回收站
│       ├── categories.py    # 分类 CRUD
│       ├── tags.py          # 标签 CRUD
│       ├── search.py        # 全文搜索
│       └── backup.py        # 备份导入导出
├── frontend/
│   └── src/
│       ├── api/             # axios 封装（request.ts + 各业务 api）
│       ├── components/      # Vue 组件（Icon, Sidebar, NoteList, NoteEditor...）
│       ├── views/           # 页面（Login, Home, Trash, Backup）
│       ├── stores/          # Pinia 状态管理
│       ├── router/          # Vue Router 配置
│       └── types/           # TypeScript 类型定义
├── docker-compose.yml
├── .env.example
└── data/                    # SQLite 数据库（运行时生成）
```

## 数据模型

```
users (id, username, password_hash, created_at)
categories (id, name, parent_id, sort_order, user_id, created_at)
notes (id, title, content, content_html, category_id, is_pinned, word_count, user_id, created_at, updated_at, deleted_at)
tags (id, name, user_id, created_at, UNIQUE(user_id, name))
note_tags (note_id, tag_id)  -- 多对多关联
```

所有业务表都有 `user_id` 列，实现多用户数据隔离。

---

## 已固化的原则（不可违反）

### 1. 用户数据隔离

**所有查询必须按 `user_id` 过滤。** 任何新增的 API 路由都必须通过 `Depends(get_current_user)` 注入当前用户，并在 SQL 查询中加 `WHERE user_id = ?`。不允许出现跨用户数据访问。

### 2. UI/UX 规范（基于 ui-ux-pro-max-skill）

每次修改前端 UI 后，必须对照 [ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) 规则审计。核心规则：

- **触摸目标 ≥ 44px**：所有可交互元素 `min-height: 44px`（移动端）
- **焦点环**：所有可交互元素必须有 `:focus-visible` 样式
- **按压反馈**：所有可点击元素必须有 `:active` 反馈（scale/颜色变化）
- **aria-label**：图标按钮必须有 `aria-label`
- **touch-action: manipulation**：消除 300ms 点击延迟
- **safe-area-inset**：移动端底部注意 `env(safe-area-inset-bottom)`
- **prefers-reduced-motion**：动画必须有降级处理
- **设计 token**：颜色/间距/圆角统一使用 CSS 变量（`--color-*`, `--space-*`, `--radius-*`），不硬编码
- **font-size ≥ 16px**：移动端输入框/下拉框 font-size 不小于 16px（防 iOS 自动放大）

### 3. 移动端适配

- 断点：`768px`，`window.innerWidth <= 768` 判定手机端
- 手机端两面板栈式导航：列表 ↔ 编辑器（`mobileView` 状态切换）
- 返回手势适配：进入编辑器时 `history.pushState()`，监听 `popstate` 切回列表
- 返回前自动保存：`switchToList` 调用 `editorRef.saveImmediately()`
- 手机端底部单行：回收站图标 + 备份图标 + 用户名 + 退出图标

### 4. 自动保存策略

- 防抖间隔 **30 秒**（减少 API 请求）
- 有未保存内容时底部显示「保存」按钮（手动保存）
- `Ctrl+S` / `Cmd+S` 快捷键立即保存
- 返回列表前触发保存（防丢失）

### 5. 安全约定

- JWT token 存 `localStorage`，axios 拦截器自动附加 `Authorization: Bearer`
- 401 响应自动清除 token 跳转登录页
- 注册三重防护：`ALLOW_REGISTRATION` 开关 + 邀请码 + IP/全局速率限制
- 密码用 bcrypt 直接哈希（不用 passlib，兼容 bcrypt>=4.0）
- AK/SK 不写入 `.tf` / `.env` 文件，通过环境变量传入

### 6. 代码风格

- 后端：每个路由文件顶部有 docstring 说明功能
- 前端：组件用 `<script setup lang="ts">`，设计 token 不硬编码
- Icon 组件统一用 `Icon.vue`，不使用 emoji
- API 响应格式：`{ code: 0, message: "success", data: ... }`

### 7. Git 约定

- 双远程：GitHub (`origin`) + GitCode (`devspace`)
- commit message 中文，格式：`type(scope): 描述`（feat/fix/chore/docs）
- 推送前先 `npm run build` 验证编译通过
- GitHub PAT 格式：`https://x-access-token:TOKEN@github.com/2Bdou/notebook.git`

---

## 开发流程

### 本地开发

```bash
# 后端
cd backend && pip install -r requirements.txt && uvicorn main:app --reload

# 前端
cd frontend && npm install && npm run dev
```

### 构建

```bash
cd frontend && npm run build  # 前端编译验证
```

### 部署

```bash
docker-compose up -d --build  # 构建并启动
```

### 新增 API 路由

1. 在 `backend/routers/` 新建文件，定义 `APIRouter`
2. 用 `Depends(get_current_user)` 注入认证
3. 所有查询加 `WHERE user_id = ?`
4. 在 `main.py` 挂载路由：`app.include_router(xxx.router, prefix="/api")`

### 新增前端页面

1. 在 `views/` 新建 `.vue` 文件
2. 在 `router/index.ts` 加路由
3. 在 `api/` 加 API 封装（如需）
4. 在 `Sidebar.vue` 和 `NoteList.vue`（手机端）加入口
5. **必须跑 UI/UX Pro Max Skill 审计**

---

## 已知决策记录

| 日期 | 决策 | 原因 |
|---|---|---|
| 2026-10-31 | 多用户改造，所有表加 user_id | 原单用户设计无法隔离数据 |
| 2026-10-31 | 注册三重防护 | 防恶意注册和暴力破解 |
| 2026-10-31 | passlib → 直接 bcrypt | passlib 与 bcrypt>=4.0 不兼容 |
| 2026-10-31 | 移动端两面板栈式导航 | 手机端三栏不可用，改为列表↔编辑器切换 |
| 2026-11-02 | 自动保存间隔 2s → 30s | 减少资源消耗，加手动保存按钮 |
| 2026-11-02 | history.pushState 适配返回手势 | iOS 边缘滑动退出应用而非返回列表 |
| 2026-11-03 | 备份导入导出功能 | 用户需数据备份和迁移能力 |
| 2026-11-03 | 端口改为 127.0.0.1:8080:80 | 适配 nginx 反代部署 |
