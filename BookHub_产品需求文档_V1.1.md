# BookHub 个人数字阅读聚合平台

版本：V1.1（经 grill-me 修订版）

文档类型：产品需求文档 (PRD)

项目名称：BookHub

项目性质：个人自用

创建日期：2026-06

---

## 1. 项目概述

### 1.1 项目名称

BookHub

### 1.2 项目定位

BookHub 是一款面向个人用户的私有化数字阅读聚合平台。

用户可通过输入书名搜索多个阅读来源，将书籍加入个人书架，并实现跨设备阅读与阅读进度同步。

本项目仅供个人学习与阅读使用，不提供公共注册、社区、商业运营及开放服务。

---

## 2. 项目目标

构建一个属于个人的数字书房。

实现以下核心能力：

- 小说搜索
- 多来源聚合
- 在线阅读
- 阅读进度同步
- 本地缓存
- 书架管理
- 多设备访问

---

## 3. 用户画像

- 用户数量：1
- 用户身份：项目拥有者本人
- 主要需求：
  1. 快速搜索并找到想读的书籍
  2. 多来源切换阅读
  3. 自动保存阅读进度，随时继续
  4. 管理个人书架
  5. 支持手机和电脑阅读
  6. 数据完全私有

---

## 4. 产品原则

### 极简
仅保留阅读相关功能。不设计：社区、评论、排行榜、点赞、社交。

### 私有化
全部数据归用户所有。支持 VPS 部署、NAS 部署、本地服务器部署。

### 离线优先
支持下载缓存、离线阅读、本地存储。

---

## 5. 产品架构

```
BookHub
├── 首页（搜索框 + 继续阅读 + 书架入口）
├── 搜索模块
├── 书籍详情
├── 阅读器（核心）
├── 书架
├── 下载中心
└── 系统设置（仅 Token 认证）
```

---

## 6. 功能需求

### 6.1 搜索模块

**功能说明**：用户输入书名后，系统聚合多个来源进行搜索。

**输入**：
- 书名
- 作者
- 关键字

**输出**：
- 书名
- 作者
- 状态（连载/完结）
- 字数
- 更新时间
- 来源标签

**功能点**：
- 模糊搜索
- 历史搜索
- 最近搜索
- 来源并行搜索 + 超时容错（8s 超时，失败来源不影响其余结果）
- 搜索结果本地缓存（TTL 6 小时）

### 6.2 书籍详情

**展示**：
- 封面
- 作者
- 简介
- 分类
- 状态
- 来源列表（可切换）

**操作**：
- 开始阅读
- 加入书架
- 下载缓存
- 切换来源

### 6.3 阅读器

**阅读设置**：
- 字号调整
- 行距调整
- 页边距
- 背景颜色（白底 / 米黄 / 灰底 / 黑底夜间）

**阅读模式**：
- 滚动模式
- 翻页模式

**夜间模式**：
- 手动切换 + 跟随系统自动切换（`prefers-color-scheme`）

**阅读记录（自动保存）**：
- 当前章节 ID
- 章节序号
- 滚动位置 / 翻页页码
- 阅读进度百分比
- 上次阅读时间
- 每 5 秒 + 切章时自动保存

**目录弹窗**：侧栏展示所有章节列表，点击跳转。

### 6.4 书架

**分组**：
- 在读
- 已完成
- 收藏/归档

**显示**：
- 封面
- 书名
- 阅读进度条
- 更新时间

**支持**：
- 排序（最近阅读 / 书名 / 加入时间）
- 删除（左滑）
- 归档

### 6.5 下载中心

**支持**：
- 单章下载
- 全书缓存（后端批量爬取，限速 0.5s/章）
- EPUB 导出（后续迭代）

**状态**：
- 下载中（进度条）
- 已完成
- 下载失败

### 6.6 认证

**方案**：部署时生成唯一 Token，写死在环境变量中。
**前端**：首次访问输入 Token，存入 localStorage，后续请求自动携带。
**后端**：全局中间件校验 Token，非公网环境可通过配置关闭。

---

## 7. 页面设计

### 首页
- 搜索框
- 最近阅读 / 继续阅读
- 书架入口

### 搜索页
- 搜索框（自动聚焦）
- 搜索历史
- 搜索结果列表 + 来源标签

### 书籍详情页
- 封面
- 简介
- 操作按钮（开始阅读 / 加入书架 / 下载）
- 来源切换列表

### 阅读页
- 正文内容（干净文本渲染）
- 目录侧栏
- 设置面板（字号/行距/背景/模式）
- 底部阅读工具栏
- 翻页 & 滚动双模式

### 书架页
- Tab 分组（在读 / 已完成 / 归档）
- 书籍列表（封面 + 进度条 + 更新时间）
- 左滑删除

---

## 8. 数据库设计

采用三表简化方案，单用户场景无需用户表。

### bookshelf

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER PK | 自增主键 |
| title | TEXT | 书名 |
| author | TEXT | 作者 |
| cover | TEXT | 封面 URL |
| intro | TEXT | 书籍简介 |
| category | TEXT | 分类 |
| status | TEXT | 书籍状态（连载/完结） |
| current_source | TEXT | 当前阅读来源标识 |
| source_data | TEXT(JSON) | 各来源进度数据，示例：`{"biquge":{"chapter_index":5,"scroll_pos":0.3,"status":"reading"},"fanqie":{"chapter_index":2,"scroll_pos":0.8,"status":"reading"}}` |
| display_status | TEXT | 展示状态：reading / finished / archived |
| last_read_at | DATETIME | 最后阅读时间 |
| created_at | DATETIME | 加入时间 |
| updated_at | DATETIME | 更新时间 |

### chapters

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER PK | 自增主键 |
| book_id | INTEGER | 关联 bookshelf.id |
| source | TEXT | 来源标识 |
| chapter_index | INTEGER | 章节序号 |
| chapter_name | TEXT | 章节名 |
| content | TEXT | 章节正文内容 |
| created_at | DATETIME | 创建时间 |

### sources

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER PK | 自增主键 |
| name | TEXT | 来源名称（展示用） |
| identifier | TEXT UNIQUE | 来源标识（代码中用） |
| base_url | TEXT | 来源站网址 |
| enabled | BOOLEAN | 是否启用 |
| healthy | BOOLEAN | 是否健康可用 |

---

## 9. 技术方案

### 前端
- **框架**：Vue 3 + TypeScript
- **构建**：Vite
- **UI 组件库**：Vant 4
- **形态**：PWA（vite-plugin-pwa）
- **支持平台**：Windows / macOS / Android / iPhone

### 后端
- **框架**：FastAPI
- **ORM**：SQLAlchemy
- **迁移工具**：Alembic

### 数据库
- **SQLite** —— 个人项目无需独立数据库服务

### 缓存
- **本地缓存策略**：
  - 搜索结果缓存（SQLite 层面）
  - 已读章节缓存（PWA Service Worker Cache API）
  - 不引入 Redis（单用户场景无必要）

### 爬虫
- **工具**：httpx / BeautifulSoup / lxml
- **架构**：统一的 `SourceProvider` 抽象接口
  - `search(keyword) -> List[BookBrief]`
  - `get_book_detail(book_id) -> BookDetail`
  - `get_chapters(book_id) -> List[Chapter]`
  - `get_chapter_content(chapter_id) -> str`
- **策略**：
  - 首次接入 2 个低难度来源（无 Cloudflare 防护）
  - 后续按需增加 adapter
  - 高反爬来源使用 Playwright 无头浏览器（单独容器运行）

### 文件存储
- 目录结构：
  ```
  /data
  ├── bookhub.db    （SQLite 数据库）
  ├── covers/       （封面缓存）
  └── downloads/    （导出文件）
  ```

---

## 10. 系统架构

```
┌─────────────────────────────────────────┐
│           前端（Vue3 + Vant 4）           │
│         PWA Service Worker              │
│     （离线缓存已读章节）                    │
│    Token → localStorage → API 请求头      │
└──────────────────┬──────────────────────┘
                   │ REST API
                   ▼
┌─────────────────────────────────────────┐
│           后端 FastAPI                    │
│                                          │
│  中间件：Token 鉴权                       │
│                                          │
│  SourceProvider 接口层                    │
│  ├── SourceAAdapter                     │
│  ├── SourceBAdapter                     │
│  └── (后续按需新增)                      │
│                                          │
│  搜索聚合器（并发 + 超时 8s + 容错）       │
│  搜索结果缓存层（TTL 6h）                 │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│            SQLite 数据库                  │
│    bookshelf / chapters / sources        │
└─────────────────────────────────────────┘
```

---

## 11. 部署方案

- **方式**：Docker Compose
- **容器**：
  - `bookhub-backend` — FastAPI 服务（含爬虫）
  - `bookhub-frontend` — Nginx 静态文件服务
- **推荐配置**：
  - CPU：2 核心
  - 内存：2GB
  - 硬盘：20GB
- **系统**：Ubuntu / Debian
- **支持环境**：VPS / NAS / 家庭服务器
- **外网访问**：Nginx 反向代理 + Token 鉴权，不暴露公网注册

---

## 12. 开发阶段规划

### 阶段一：基础设施 + 爬虫核心

**目标**：后端跑起来，能搜书、能看详情，全链路调通。

**后端：**
- FastAPI 项目初始化 + SQLite + SQLAlchemy + Alembic
- 数据库建表（bookshelf / chapters / sources）
- SourceProvider 抽象接口定义
- 接入 2 个低难度来源站
- 搜索聚合逻辑（并发 + 8s 超时 + 容错）
- 搜索结果本地缓存
- Token 鉴权中间件

**前端：**
- Vite + Vue3 + TypeScript + Vant 4 + PWA 脚手架
- 路由骨架（首页 / 搜索 / 书籍详情 / 阅读器 / 书架）
- Token 登录页
- API 请求封装

**部署：**
- Dockerfile（后端）+ nginx.conf（前端）
- docker-compose.yml

**交付物**：`docker-compose up` 后能搜书、看到书籍详情。

---

### 阶段二：首页 + 搜索 + 书籍详情

**目标**：用户核心交互链路走通。

**页面开发：**

| 页面 | 功能 | 核心 Vant 组件 |
|---|---|---|
| 首页 | 搜索框 + 继续阅读 + 书架入口 | van-search, van-cell |
| 搜索页 | 搜索框 + 历史 + 结果列表 + 来源标签 | van-search, van-list, van-tag |
| 书籍详情页 | 封面/简介 + 来源切换 + 操作按钮 | van-image, van-tabs, van-button |

**后端 API：**
- `GET /api/search?keyword=&source=`
- `GET /api/books/{id}`
- `GET /api/sources`

**交付物**：能搜书、查看详情、切换来源。

---

### 阶段三：阅读器（核心攻坚）

**目标**：流畅的阅读体验。

**阅读器功能：**
- 章节内容展示（干净文本渲染）
- 目录弹窗（van-sidebar）
- 翻页模式（左右滑动切章节）
- 滚动模式（连续长滚动）
- 字号 / 行距 / 边距调整（van-slider，实时生效）
- 背景颜色切换（白底 / 米黄 / 灰底 / 夜间黑底）
- 夜间模式跟随系统
- 阅读进度自动保存（5s 间隔 + 切章触发）
- 底部工具栏

**后端 API：**
- `GET /api/chapters/{id}`
- `GET /api/chapters?book_id=&source=`
- `POST /api/progress`
- `GET /api/progress?book_id=&source=`

**交付物**：能流畅看完一本书，设置持久化，进度自动保存。

---

### 阶段四：书架 + 下载中心 + PWA 离线

**目标**：管理书籍集合，支持离线阅读。

**书架页：**
- Tab 分组：在读 / 已完成 / 归档（van-tabs）
- 列表展示：封面 + 进度条 + 更新时间
- 左滑删除（van-swipe-cell）

**下载中心：**
- 全书缓存（后端批量爬取，限速 0.5s/章）
- 下载状态展示（van-progress）

**PWA 离线：**
- Service Worker 注册
- Cache API 缓存已读章节
- manifest.json 配置

**后端 API：**
- `GET /api/bookshelf`
- `POST /api/bookshelf`（加入书架）
- `DELETE /api/bookshelf/{id}`
- `PATCH /api/bookshelf/{id}`（更新状态）
- `POST /api/download/{book_id}`
- `GET /api/download/{book_id}/status`

**交付物**：书架管理 + 下载全书离线阅读。

---

### 阶段五：打磨与收尾

**目标**：修边角、稳定体验。

- 阅读器手势优化（灵敏度、防误触）
- 加载状态 / 空状态 / 错误状态全覆盖
- 搜索历史持久化（localStorage）
- 来源不可用时的用户提示与自动降级
- 夜间模式跟随系统（`prefers-color-scheme`）
- favicon + PWA 图标 + 应用名
- 部署文档 + 来源适配器接入文档
- Docker Compose 生产环境配置完善

**交付物**：一个你自己愿意天天用的产品。

---

## 13. 后续规划

### V2
- AI 章节总结
- 人物关系分析
- 剧情回顾

### V3
- 本地大模型适配（Ollama）
- 智能推荐（基于已读书籍分类/作者/标签）
- 阅读统计（阅读时长、读完本数等）

---

## 14. 项目总结

BookHub 的目标并不是成为一个小说网站。而是：

> **"打造一个完全属于自己的私人数字书房。"**

核心价值：
- 私有化 —— 数据完全归你所有
- 聚合阅读 —— 多来源一站搜书
- 多设备同步 —— 手机电脑无缝切换
- 长期收藏 —— 构建个人阅读库
- 数据自主 —— 不受任何平台限制

最终产品形态类似个人版的媒体服务器，只不过管理对象从影视变成了阅读内容。