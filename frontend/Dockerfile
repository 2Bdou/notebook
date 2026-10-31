# ===== 阶段1：构建前端资源 =====
FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
# 优先使用 lock 文件安装，无 lock 时回退到普通安装
RUN npm ci || npm install

COPY . .
RUN npm run build

# ===== 阶段2：Nginx 托管静态文件 =====
FROM nginx:alpine

# 拷贝构建产物到 Nginx 静态目录
COPY --from=builder /app/dist /usr/share/nginx/html
# 覆盖默认 Nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
