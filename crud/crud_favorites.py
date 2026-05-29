from sqlalchemy import func
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.models_favorit import Favorite
from models.model_news import News

# 获取收藏
async def get_favorite(db: AsyncSession, user_id: int, news_id: int):
    query = select(Favorite).where(Favorite.user_id == user_id, Favorite.news_id == news_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def add_favorite(db: AsyncSession,
                       user_id: int, 
                       news_id: int):
    favorite = Favorite(user_id=user_id, news_id=news_id)
    db.add(favorite)
    await db.commit()
    await db.refresh(favorite)
    return favorite

async def list_favorites(db: AsyncSession, 
                         user_id: int, 
                         page: int = 1, 
                         page_size: int = 10):
    conut_query = select(func.count()).select_from(Favorite).where(Favorite.user_id == user_id)
    count = await db.execute(conut_query)
    total = count.scalar_one()# 获取收藏总数
    offset = (page - 1) * page_size
    query = (
        select(Favorite, News)
        .join(News, Favorite.news_id == News.id)
        .where(Favorite.user_id == user_id)
        .order_by(Favorite.created_at.desc())  # 按收藏时间倒序
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(query)
    return result.all(),total

async def remove_favorite(db: AsyncSession, 
                          user_id: int, 
                          news_id: int):
    query = select(Favorite).where(Favorite.user_id == user_id, Favorite.news_id == news_id)
    result = await db.execute(query)
    favorite = result.scalar_one_or_none()
    if favorite:
        await db.delete(favorite)
        await db.commit()

async def clear_favorites(db: AsyncSession, user_id: int):
    query = select(Favorite).where(Favorite.user_id == user_id)
    result = await db.execute(query)
    favorites = result.scalars().all()
    i=0
    for favorite in favorites:
        await db.delete(favorite)
        i+=1
    await db.commit()
    return i