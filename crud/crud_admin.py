from sqlalchemy import func, select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from models.model_users import User, User_token
from models.model_news import News, Category
from models.models_favorit import Favorite
from models.models_history import History
from schemas import schemas_admin


# ========== Dashboard ==========
async def get_dashboard_stats(db: AsyncSession) -> schemas_admin.DashboardStats:
    total_users = await db.scalar(select(func.count(User.id)))
    total_news = await db.scalar(select(func.count(News.id)))
    total_views = await db.scalar(select(func.coalesce(func.sum(News.views), 0)))
    total_categories = await db.scalar(select(func.count(Category.id)))
    return schemas_admin.DashboardStats(
        total_users=total_users,
        total_news=total_news,
        total_views=total_views,
        total_categories=total_categories,
    )


# ========== User Management ==========
async def admin_get_users(db: AsyncSession, page: int, page_size: int) -> tuple[list[User], int]:
    offset = (page - 1) * page_size
    total = await db.scalar(select(func.count(User.id)))
    stmt = select(User).order_by(User.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(stmt)
    users = result.scalars().all()
    return list(users), total


async def admin_get_user(db: AsyncSession, user_id: int) -> User | None:
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


async def admin_update_user(db: AsyncSession, user_id: int, data: schemas_admin.AdminUserUpdate) -> User:
    user = await admin_get_user(db, user_id)
    update_data = data.model_dump(exclude_unset=True, exclude_none=True)
    for key, value in update_data.items():
        setattr(user, key, value)
    await db.commit()
    await db.refresh(user)
    return user


async def admin_delete_user(db: AsyncSession, user_id: int) -> bool:
    user = await admin_get_user(db, user_id)
    # 删除关联数据
    await db.execute(delete(User_token).where(User_token.user_id == user_id))
    await db.execute(delete(Favorite).where(Favorite.user_id == user_id))
    await db.execute(delete(History).where(History.user_id == user_id))
    await db.delete(user)
    await db.commit()
    return True


# ========== News Management ==========
async def admin_get_news_list(
    db: AsyncSession,
    page: int,
    page_size: int,
    category_id: int | None = None,
    keyword: str | None = None,
    status: str | None = None,
) -> tuple[list[News], int]:
    offset = (page - 1) * page_size

    conditions = []
    if category_id is not None:
        conditions.append(News.category_id == category_id)
    if keyword:
        conditions.append(News.title.contains(keyword))
    if status:
        conditions.append(News.status == status)

    count_stmt = select(func.count(News.id))
    if conditions:
        count_stmt = count_stmt.where(*conditions)
    total = await db.scalar(count_stmt)

    stmt = select(News).order_by(News.created_at.desc()).offset(offset).limit(page_size)
    if conditions:
        stmt = stmt.where(*conditions)
    result = await db.execute(stmt)
    return list(result.scalars().all()), total


async def admin_get_news_detail(db: AsyncSession, news_id: int) -> News:
    stmt = select(News).where(News.id == news_id)
    result = await db.execute(stmt)
    news = result.scalar_one_or_none()
    if not news:
        raise HTTPException(status_code=404, detail="新闻不存在")
    return news


async def admin_create_news(db: AsyncSession, data: schemas_admin.AdminNewsCreate) -> News:
    news = News(
        title=data.title,
        description=data.description,
        content=data.content,
        image=data.image,
        author=data.author,
        category_id=data.category_id,
        publish_time=data.publish_time or func.now(),
        source_url=data.source_url,
    )
    db.add(news)
    await db.commit()
    await db.refresh(news)
    return news


async def admin_update_news(db: AsyncSession, news_id: int, data: schemas_admin.AdminNewsUpdate) -> News:
    news = await admin_get_news_detail(db, news_id)
    update_data = data.model_dump(exclude_unset=True, exclude_none=True)
    for key, value in update_data.items():
        setattr(news, key, value)
    await db.commit()
    await db.refresh(news)
    return news


async def admin_delete_news(db: AsyncSession, news_id: int) -> bool:
    news = await admin_get_news_detail(db, news_id)
    await db.execute(delete(Favorite).where(Favorite.news_id == news_id))
    await db.execute(delete(History).where(History.news_id == news_id))
    await db.delete(news)
    await db.commit()
    try:
        from utils import vector_store
        vector_store.remove_news(news_id)
    except Exception:
        pass
    return True


# ========== Category Management ==========
async def admin_get_categories(db: AsyncSession) -> list[Category]:
    stmt = select(Category).order_by(Category.sort_order)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def admin_create_category(db: AsyncSession, data: schemas_admin.AdminCategoryCreate) -> Category:
    cat = Category(name=data.name, sort_order=data.sort_order)
    db.add(cat)
    await db.commit()
    await db.refresh(cat)
    return cat


async def admin_update_category(db: AsyncSession, category_id: int, data: schemas_admin.AdminCategoryUpdate) -> Category:
    stmt = select(Category).where(Category.id == category_id)
    result = await db.execute(stmt)
    cat = result.scalar_one_or_none()
    if not cat:
        raise HTTPException(status_code=404, detail="分类不存在")
    update_data = data.model_dump(exclude_unset=True, exclude_none=True)
    for key, value in update_data.items():
        setattr(cat, key, value)
    await db.commit()
    await db.refresh(cat)
    return cat


async def admin_delete_category(db: AsyncSession, category_id: int) -> bool:
    stmt = select(Category).where(Category.id == category_id)
    result = await db.execute(stmt)
    cat = result.scalar_one_or_none()
    if not cat:
        raise HTTPException(status_code=404, detail="分类不存在")
    news_count = await db.scalar(select(func.count(News.id)).where(News.category_id == category_id))
    if news_count > 0:
        raise HTTPException(status_code=400, detail="该分类下还有新闻，无法删除")
    await db.delete(cat)
    await db.commit()
    return True


# ========== 批量导入 ==========
async def admin_batch_import(
    db: AsyncSession, items: list[schemas_admin.ImportNewsItem]
) -> schemas_admin.ImportResult:
    """
    批量导入新闻（爬虫/JSON导入共用）
    去重逻辑: 基于 sourceUrl 检查是否已存在，已存在则跳过
    导入状态: 全部存为 draft（待审核），需管理员审核通过后才对用户可见
    返回: ImportResult(total=总数, imported=成功数, skipped=跳过数, errors=错误列表)
    """
    imported = 0
    skipped = 0
    errors = []

    for i, item in enumerate(items):
        try:
            url = item.sourceUrl
            # URL 去重
            if url:
                existing = await db.scalar(
                    select(func.count(News.id)).where(News.source_url == url)
                )
                if existing > 0:
                    skipped += 1
                    continue

            # 发布日期解析
            publish_time = None
            if item.publishTime:
                try:
                    publish_time = __import__("datetime").datetime.strptime(
                        item.publishTime, "%Y-%m-%dT%H:%M:%S"
                    )
                except ValueError:
                    publish_time = func.now()
            else:
                publish_time = func.now()

            img = item.image.strip() if item.image else None
            desc = item.description or ""
            content = item.content or item.description or item.title
            news = News(
                title=item.title,
                description=desc,
                content=content,
                image=img if img else None,
                author=item.author or "",
                category_id=item.categoryId,
                source_url=url,
                status="draft",
                publish_time=publish_time or func.now(),
            )
            db.add(news)
            imported += 1
        except Exception as e:
            errors.append(f"第{i+1}条({item.title[:20]})导入失败: {str(e)}")

    await db.commit()
    return schemas_admin.ImportResult(
        total=len(items), imported=imported, skipped=skipped, errors=errors
    )


# ========== 审核管理 ==========
async def admin_get_pending_news(
    db: AsyncSession, page: int, page_size: int
) -> tuple[list[News], int]:
    """获取待审核新闻列表（status=draft），按创建时间倒序"""
    offset = (page - 1) * page_size
    base = select(News).where(News.status == "draft")
    total = await db.scalar(select(func.count()).select_from(base.subquery()))
    stmt = select(News).where(News.status == "draft").order_by(News.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(stmt)
    return list(result.scalars().all()), total


async def admin_approve_news(db: AsyncSession, news_id: int) -> News:
    """
    审核通过一篇新闻
    操作: status = "published" → 用户端可见
    副作用: 自动调用 vector_store.index_news() 将新闻加入 AI 检索索引
    """
    news = await admin_get_news_detail(db, news_id)
    news.status = "published"
    await db.commit()
    await db.refresh(news)
    # 自动索引到向量库，使 AI 问答能检索到这篇新新闻
    try:
        from utils import vector_store
        vector_store.index_news(
            news_id=news.id,
            title=news.title,
            content=news.content,
            metadata={
                "category": str(news.category_id),
                "author": news.author or "",
                "publish_time": str(news.publish_time) if news.publish_time else "",
            },
        )
    except Exception:
        pass
    return news


async def admin_reject_news(db: AsyncSession, news_id: int) -> bool:
    """
    驳回一篇待审核新闻（直接删除）
    副作用: 自动调用 vector_store.remove_news() 从 AI 索引中移除
    """
    news = await admin_get_news_detail(db, news_id)
    await db.delete(news)
    await db.commit()
    try:
        from utils import vector_store
        vector_store.remove_news(news_id)
    except Exception:
        pass
    return True
