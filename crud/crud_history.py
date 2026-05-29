from datetime import datetime, timedelta
import uuid
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from models.model_news import News
from utils import securit
from models.models_history import History
from schemas import schemas_history
from fastapi import HTTPException


async def get_history(db: AsyncSession, user_id: int):
    query = select(History).where(History.user_id == user_id)
    result = await db.execute(query)
    return result.scalars().all()

async def add_history(
        db: AsyncSession,
        user_id: int,
        news_id: int
        ):
    query = History(user_id=user_id, news_id=news_id)
    db.add(query)
    await db.commit()
    await db.refresh(query)
    return query

async def list_history(
        db: AsyncSession,
        user_id: int,
        page: int = 1,
        page_size: int = 10
        ):
    conut_query = select(func.count()).select_from(History).where(History.user_id == user_id)
    count = await db.execute(conut_query)# 获取收藏总数
    total = count.scalar_one()
    offset = (page - 1) * page_size
    query = (
        select(History, News)
        .join(News, History.news_id == News.id)
        .where(History.user_id == user_id)
        .order_by(History.view_time.desc())  # 按收藏时间倒序
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(query)
    return result.all(),total

async def remove_history(
        db: AsyncSession,
        user_id: int,
        news_id: int
        ):
    query = select(History).where(History.user_id == user_id, History.news_id == news_id)
    result = await db.execute(query)
    history = result.scalar_one_or_none()
    if history:
        await db.delete(history)
        await db.commit()

async def clear_history(
        db: AsyncSession,
        user_id: int
        ):
    query = select(History).where(History.user_id == user_id)
    result = await db.execute(query)
    history = result.scalars().all()
    for item in history:
        await db.delete(item)
    await db.commit()
