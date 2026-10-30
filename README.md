# 📓 Notebook — Markdown 记事本

一个轻量级的 Markdown 笔记应用，支持分类管理、标签筛选、全文搜索和回收站。

## ✨ 功能

- **笔记管理**：增删改查、软删除 + 回收站、置顶
- **Markdown 编辑**：实时预览、代码语法高亮、图片粘贴、暗色模式
- **分类管理**：树形结构、新建/重命名/删除、按分类过滤
- **标签管理**：多标签、按标签过滤、笔记计数
- **搜索**：全文搜索（标题 + 正文）、关键词高亮、相关度排序
- **列表排序**：更新时间/创建时间/标题/字数，升序/降序

## 🛠️ 技术栈

| 层 | 技术 |
|----|------|
| 前端 | Vue 3 + Vite + TypeScript + Pinia + md-editor-v3 |
| 后端 | Python FastAPI + aiosqlite |
| 数据库 | SQLite |
| 部署 | Docker Compose + Nginx |

## 🚀 本地开发

### 后端

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

前端开发服务器自动代理 `/api` 到 `http://localhost:8000`。

## 🐳 Docker 部署

```bash
# 构建并启动
docker compose up -d --build

# 查看状态
docker compose ps

# 停止
docker compose down
```

## 📁 项目结构

```
notebook/
├── backend/          # FastAPI 后端
│   ├── main.py       # 入口
│   ├── database.py   # SQLite 连接管理 + 建表
│   ├── models/       # 数据访问层
│   ├── routers/      # API 路由
│   └── schemas/      # Pydantic 模型
├── frontend/         # Vue 3 前端
│   ├── src/
│   │   ├── api/      # API 封装
│   │   ├── stores/   # Pinia 状态管理
│   │   ├── views/    # 页面
│   │   ├── components/ # 组件
│   │   └── utils/    # 工具函数
│   ├── Dockerfile    # 多阶段构建
│   └── nginx.conf    # Nginx 配置
└── data/             # SQLite 数据（gitignore）
```

## 📝 API 文档

启动后端后访问 `http://localhost:8000/docs` 查看 Swagger 交互式 API 文档。
