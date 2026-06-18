from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from routers import news
from routers import users
from routers import favorite
from routers import history
from routers import admin
from routers import ai
from utils.exception_handlers import register_exception_handlers

app=FastAPI()

register_exception_handlers(app)

origins=[
    "http://localhost",
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    "http://localhost:5176",
    "http://localhost:5177",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 允许的源
    allow_credentials=True, # 允许携带cookie
    allow_methods=["*"],    # 允许的请求方法
    allow_headers=["*"],    # 允许的请求头
)

@app.get('/')
async def root():
    return {"message":"Hello World"}

app.include_router(news.router)
app.include_router(users.router)
app.include_router(favorite.router)
app.include_router(history.router)
app.include_router(admin.router)
app.include_router(ai.router)


@app.on_event("startup")
async def startup_index_news():
    """启动时如果没有索引，则全量索引所有已发布新闻"""
    try:
        from utils import vector_store
        if not vector_store.is_indexed():
            import asyncio
            from config.db_config import AsyncSessionLocal
            from sqlalchemy import select
            from models.model_news import News

            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(News).where(News.status == "published")
                )
                news_list = result.scalars().all()
                if news_list:
                    items = [
                        {
                            "id": n.id,
                            "title": n.title,
                            "content": n.content,
                            "author": n.author or "",
                            "category": str(n.category_id),
                            "publish_time": str(n.publish_time) if n.publish_time else "",
                        }
                        for n in news_list
                    ]
                    count = vector_store.index_all_news(items)
                    print(f"[向量库] 全量索引完成: {count} 篇新闻")
    except Exception as e:
        print(f"[向量库] 初始化跳过: {e}")
