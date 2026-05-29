from sqlalchemy import func, update
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.model_news import Category, News


async def get_categories(db:AsyncSession,skip: int = 0, limit: int = 10):
    stmt=select(Category).offset(skip).limit(limit)
    result=await db.execute(stmt)
    return result.scalars().all()

async def get_news_list(db:AsyncSession,
                        category_id: int ,
                        page: int = 0,
                        pageSize: int = 10
                        ):
    # 查询的是指定分类下的所有新闻
    stmt=select(News).where(News.category_id ==category_id).offset(page).limit(pageSize)
    result=await db.execute(stmt)
    return result.scalars().all()

async def get_news_count(db:AsyncSession,
                         category_id: int
                         ):
    """
    获取指定分类下的新闻数量
    """
    stmt=select(func.count(News.id)).where(News.category_id ==category_id)
    result=await db.execute(stmt)
    return result.scalar_one()#只能有单个结果,否则报错

async def get_news_detail(db:AsyncSession,
                          news_id: int
                          ):
    """
    获取新闻详情
    """
    # 浏览量+1
    await db.execute(
        update(News)
        .where(News.id == news_id)
        .values(views=News.views + 1)
    )
    await db.commit()
    # 查询新闻详情
    stmt=select(News).where(News.id ==news_id)
    result=await db.execute(stmt)
    return result.scalar_one_or_none()

async def detail_relatedNews(db:AsyncSession,
                            category_id: int ,
                            id: int,
                            pageSize: int = 5
                            ):
    # 查询的是指定分类下的所有新闻
    stmt=select(News).where(News.category_id ==category_id,News.id!=id).order_by(
        News.views.desc()   #按点击数降序排
    ).limit(pageSize)
    result=await db.execute(stmt)
    return result.scalars().all()