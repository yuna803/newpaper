# 新闻资讯平台

基于 FastAPI + Vue3 的新闻资讯系统，包含用户端、管理后台、AI 问答和新闻爬虫。

## 项目结构

```
├── main.py                    # FastAPI 入口
├── migrate_add_role.py        # 数据库迁移脚本
├── config/                    # 数据库配置
├── models/                    # SQLAlchemy 数据模型
│   ├── base.py                # 统一 Base 类
│   ├── model_users.py         # 用户 + Token
│   ├── model_news.py          # 新闻 + 分类
│   ├── models_favorit.py      # 收藏
│   └── models_history.py      # 浏览历史
├── crud/                      # 数据库操作
│   ├── crud_users.py          # 用户 CRUD
│   ├── crud_news.py           # 新闻 CRUD + 搜索
│   ├── crud_admin.py          # 管理员 CRUD + 审核 + 批量导入
│   ├── crud_favorites.py      # 收藏 CRUD
│   └── crud_history.py        # 历史 CRUD
├── routers/                   # API 路由
│   ├── users.py               # 用户接口 (/api/user)
│   ├── news.py                # 新闻接口 (/api/news)
│   ├── favorite.py            # 收藏接口 (/api/favorite)
│   ├── history.py             # 历史接口 (/api/history)
│   ├── admin.py               # 管理接口 (/api/admin)
│   └── ai.py                  # AI 问答 (/api/ai)
├── schemas/                   # Pydantic 数据校验
├── utils/                     # 工具模块
│   ├── auth.py                # Token 认证 + 管理员鉴权
│   ├── securit.py             # bcrypt 密码加密
│   ├── response.py            # 统一响应格式
│   ├── vector_store.py        # FAISS 向量库 (AI 检索)
│   └── exception_handlers.py  # 全局异常处理
├── scraper/                   # 新闻爬虫
│   └── netease_scraper.py     # 新浪新闻爬虫
├── xwzx-news/                 # 用户端前端 (Vue3 + Vant)
├── admin-frontend/            # 管理后台 (Vue3 + Element Plus)
└── chroma_db/                 # FAISS 索引持久化目录
```

## 快速开始

### 环境要求

- Python 3.13+
- MySQL 8.0+
- Node.js 18+

### 1. 数据库

创建数据库并配置连接信息（`config/db_config.py`）：

```python
ASYNC_DATABASE_URL = "mysql+aiomysql://root:密码@localhost:3306/news_app?charset=utf8mb4"
```

### 2. 后端

```bash
# 安装依赖
pip install fastapi uvicorn sqlalchemy aiomysql pymysql bcrypt passlib pydantic faiss-cpu openai

# 数据库迁移（添加 role、status 等字段，创建默认管理员）
python migrate_add_role.py

# 设置 AI API Key
set DASHSCOPE_API_KEY=你的阿里云DashScope密钥

# 启动后端（首次启动会自动索引全部新闻到 FAISS）
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### 3. 用户端前端

```bash
cd xwzx-news
npm install
npm run dev          # 默认 http://localhost:5173
```

### 4. 管理后台

```bash
cd admin-frontend
npm install
npm run dev          # 默认 http://localhost:5174
```

**默认管理员**：`admin` / `admin123`

## API 文档

### 用户端

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/user/register | 用户注册 |
| POST | /api/user/login | 用户登录 |
| GET | /api/user/info | 获取用户信息 |
| PUT | /api/user/update | 修改用户资料 |
| PUT | /api/user/password | 修改密码 |
| GET | /api/news/categories | 新闻分类列表 |
| GET | /api/news/list | 新闻列表（按分类分页） |
| GET | /api/news/detail | 新闻详情 |
| GET | /api/news/search | 全局搜索（按标题） |
| POST | /api/favorite/add | 添加收藏 |
| GET | /api/favorite/list | 收藏列表 |
| GET | /api/favorite/check | 检查收藏状态 |
| DELETE | /api/favorite/remove | 取消收藏 |
| POST | /api/history/add | 添加浏览记录 |
| GET | /api/history/list | 浏览历史 |

### 管理端

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/admin/dashboard | 数据统计 |
| GET | /api/admin/news | 新闻列表（支持状态/分类/关键词筛选） |
| GET | /api/admin/news/{id} | 新闻详情 |
| POST | /api/admin/news | 创建新闻 |
| PUT | /api/admin/news/{id} | 编辑新闻 |
| DELETE | /api/admin/news/{id} | 删除新闻 |
| POST | /api/admin/news/import | JSON 批量导入 |
| POST | /api/admin/news/scrape | 一键爬取新浪新闻 |
| GET | /api/admin/news/pending | 待审核列表 |
| PUT | /api/admin/news/{id}/approve | 审核通过 |
| DELETE | /api/admin/news/{id}/reject | 驳回（删除） |
| POST | /api/admin/news/batch-approve | 批量通过 |
| POST | /api/admin/news/batch-reject | 批量驳回 |
| GET | /api/admin/users | 用户列表 |
| PUT | /api/admin/users/{id} | 修改用户 |
| DELETE | /api/admin/users/{id} | 删除用户 |
| GET | /api/admin/categories | 分类列表 |
| POST | /api/admin/categories | 创建分类 |
| PUT | /api/admin/categories/{id} | 编辑分类 |
| DELETE | /api/admin/categories/{id} | 删除分类 |

### AI 问答

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/ai/chat | RAG 聊天（SSE 流式） |

## 新闻爬虫

```bash
# 命令行使用
python scraper/netease_scraper.py -n 20 -o news.json    # 爬 20 条
python scraper/netease_scraper.py --channel tech -n 10   # 科技频道
python scraper/netease_scraper.py --channel sports -n 15 # 体育频道

# 频道选项: all / finance / tech / sports / ent / world
```

**分类映射**：

| 爬虫频道 | 数据库分类 |
|----------|-----------|
| 财经 → | 财经 (id=8) |
| 科技 → | 科技 (id=7) |
| 体育 → | 体育 (id=6) |
| 娱乐 → | 娱乐 (id=5) |
| 国际 → | 国际 (id=4) |

也可以直接在管理后台 → 导入新闻 → 一键爬取，选择频道和数量，勾选"深度抓取正文"自动逐篇抓取完整文章内容。

## AI 问答架构

```
用户提问 → xwzx-news → /api/ai/chat
  → FAISS 语义检索 5 篇最相关新闻
  → 拼接上下文 → Qwen3-max 生成回答
  → SSE 流式返回
```

- **向量模型**：DashScope text-embedding-v4（1024维）
- **对话模型**：Qwen3-max
- **分片策略**：一篇新闻 = 一个文档
- **增量索引**：审核通过自动加入 FAISS，删除/驳回自动移除

## 审核工作流

```
爬虫抓取 → 保存为草稿 → 管理员审核 → 通过(发布+入向量库) / 驳回(删除)
```

- 草稿新闻不对用户可见
- 审核通过后自动加入 AI 检索索引
- 支持批量通过/驳回
- 导入时基于 sourceUrl 自动去重

## 技术栈

| 层 | 技术 |
|----|------|
| 后端框架 | FastAPI (Python) |
| 数据库 | MySQL + SQLAlchemy (异步) |
| 向量库 | FAISS |
| AI | DashScope (Qwen3-max + text-embedding-v4) |
| 用户端前端 | Vue3 + Vant + Pinia + Vue Router |
| 管理后台 | Vue3 + Element Plus + Pinia + Vue Router |
| 爬虫 | requests + BeautifulSoup |
