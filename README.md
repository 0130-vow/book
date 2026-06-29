# BookHub

BookHub 是一个单用户、可私有部署的数字阅读聚合平台。它提供聚合搜索、书籍详情、在线阅读、阅读进度同步、书架管理、全书离线缓存和 PWA 安装能力。

## 功能

- Token 单用户认证
- 多书源并发搜索、8 秒超时容错、6 小时搜索缓存
- 响应式书籍详情、书架和下载中心
- 滚动/翻页阅读模式，字号、行距、页边距和四种背景
- 每 5 秒自动保存章节和阅读位置
- PWA 章节缓存与全书服务端缓存
- FastAPI + SQLAlchemy + SQLite
- Vue 3 + TypeScript + Vant 4

当前内置两个来源：

- 中文公版书库：随服务部署，可离线使用
- Project Gutenberg：通过 Gutendex API 搜索并读取公版电子书

旧版重复演示镜像升级后会自动停用，不影响已有书架中的 `classics-a` 记录。

## 快速启动

```bash
cp .env.example .env
# 修改 .env 中的 BOOKHUB_TOKEN
docker compose up -d --build
```

默认只监听 `127.0.0.1:8090`，不会直接暴露公网。健康检查：

```bash
curl http://127.0.0.1:8090/api/health
```

## Cloudflare Tunnel

在 Cloudflare Zero Trust 中为已有 Tunnel 增加 Public Hostname：

- Service type: `HTTP`
- URL: `127.0.0.1:8090`
- 推荐域名: `book.vowcc.com`

BookHub 自身仍会校验 `.env` 中的 Token。

## 本地开发

后端：

```bash
cd backend
python -m venv .venv
pip install -r requirements.txt
uvicorn app.main:app --reload
```

前端：

```bash
cd frontend
pnpm install
pnpm dev
```

Vite 会将 `/api` 代理到 `127.0.0.1:8000`。

## 书源适配

实现 `backend/app/providers/base.py` 中的 `SourceProvider`，再在 `backend/app/providers/__init__.py` 注册实例即可。每个书源需要提供搜索、详情、目录和章节正文四个方法。外部正文 URL 应限制可信域名，HTTP 异常应转换为明确的上游错误。请遵守来源站点的服务条款、robots 规则和内容版权要求。

## 数据

SQLite、章节正文和下载任务保存在 Docker volume `bookhub-data`。升级容器不会删除数据；需要迁移时可在后端目录运行：

```bash
alembic upgrade head
```
