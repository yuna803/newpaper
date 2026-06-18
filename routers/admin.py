from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from config import db_config
from crud import crud_admin
from models.model_users import User
from schemas import schemas_admin
from utils.auth import get_current_admin
from utils.response import success_response

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ========== Dashboard ==========
# ========== 仪表盘 ==========
@router.get("/dashboard")
async def get_dashboard(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(db_config.get_db),
):
    stats = await crud_admin.get_dashboard_stats(db)
    return success_response(message="获取成功", data=stats)


# ========== 用户管理 ==========
@router.get("/users")
async def admin_list_users(
    page: int = Query(1, alias="page"),
    pageSize: int = Query(10, alias="pageSize", le=100),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(db_config.get_db),
):
    users, total = await crud_admin.admin_get_users(db, page, pageSize)
    return success_response(
        message="获取成功",
        data=schemas_admin.AdminUserListResponse(
            list=[schemas_admin.AdminUserInfo.model_validate(u) for u in users],
            total=total,
            page=page,
            pageSize=pageSize,
        ),
    )


@router.put("/users/{user_id}")
async def admin_update_user_info(
    user_id: int,
    user_data: schemas_admin.AdminUserUpdate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(db_config.get_db),
):
    user = await crud_admin.admin_update_user(db, user_id, user_data)
    return success_response(message="修改成功", data=schemas_admin.AdminUserInfo.model_validate(user))


@router.delete("/users/{user_id}")
async def admin_delete_user_route(
    user_id: int,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(db_config.get_db),
):
    await crud_admin.admin_delete_user(db, user_id)
    return success_response(message="删除成功")


# ========== 新闻管理 ==========
@router.get("/news")
async def admin_list_news(
    page: int = Query(1, alias="page"),
    pageSize: int = Query(10, alias="pageSize", le=100),
    categoryId: int | None = Query(None, alias="categoryId"),
    keyword: str | None = Query(None, alias="keyword"),
    status: str | None = Query(None, alias="status"),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(db_config.get_db),
):
    news_list, total = await crud_admin.admin_get_news_list(db, page, pageSize, categoryId, keyword, status)
    return success_response(
        message="获取成功",
        data=schemas_admin.AdminNewsListResponse(
            list=[schemas_admin.AdminNewsInfo.model_validate(n) for n in news_list],
            total=total,
            page=page,
            pageSize=pageSize,
        ),
    )


@router.get("/news/pending")
async def admin_list_pending(
    page: int = Query(1, alias="page"),
    pageSize: int = Query(10, alias="pageSize", le=100),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(db_config.get_db),
):
    news_list, total = await crud_admin.admin_get_pending_news(db, page, pageSize)
    return success_response(
        message="获取成功",
        data=schemas_admin.AdminNewsListResponse(
            list=[schemas_admin.AdminNewsInfo.model_validate(n) for n in news_list],
            total=total,
            page=page,
            pageSize=pageSize,
        ),
    )


@router.get("/news/{news_id}")
async def admin_get_news(
    news_id: int,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(db_config.get_db),
):
    news = await crud_admin.admin_get_news_detail(db, news_id)
    return success_response(message="获取成功", data=schemas_admin.AdminNewsInfo.model_validate(news))


@router.post("/news")
async def admin_create_news_route(
    news_data: schemas_admin.AdminNewsCreate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(db_config.get_db),
):
    news = await crud_admin.admin_create_news(db, news_data)
    return success_response(message="创建成功", data=schemas_admin.AdminNewsInfo.model_validate(news))


# ========== 一键爬取 ==========
@router.post("/news/scrape")
async def admin_scrape_news(
    channel: str = Query("all", alias="channel"),
    count: int = Query(40, alias="count", le=100),
    deep: bool = Query(False, alias="deep"),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(db_config.get_db),
):
    import asyncio
    from scraper.netease_scraper import fetch_sina_news

    channel_lid_map = {
        "all": [2509, 2510, 2511, 2669, 2514],
        "finance": [2509],
        "tech": [2510, 2515, 2970],
        "sports": [2511, 2968],
        "ent": [2669, 2513],
        "world": [2514],
    }
    lids = channel_lid_map.get(channel, [2509, 2510, 2511, 2669, 2514])

    loop = asyncio.get_running_loop()
    items = await loop.run_in_executor(None, lambda: fetch_sina_news(count, lids, deep))

    import_items = [schemas_admin.ImportNewsItem(**item) for item in items]
    result = await crud_admin.admin_batch_import(db, import_items)
    return success_response(
        message=f"爬取完成：成功{result.imported}条，跳过{result.skipped}条",
        data=result,
    )


@router.post("/news/import")
async def admin_import_news(
    items: list[schemas_admin.ImportNewsItem],
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(db_config.get_db),
):
    result = await crud_admin.admin_batch_import(db, items)
    return success_response(message=f"导入完成：成功{result.imported}条，跳过{result.skipped}条", data=result)


@router.put("/news/{news_id}/approve")
async def admin_approve_news_route(
    news_id: int,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(db_config.get_db),
):
    news = await crud_admin.admin_approve_news(db, news_id)
    return success_response(message="审核通过", data=schemas_admin.AdminNewsInfo.model_validate(news))


@router.post("/news/batch-approve")
async def admin_batch_approve(
    ids: list[int],
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(db_config.get_db),
):
    approved = []
    for news_id in ids:
        try:
            news = await crud_admin.admin_approve_news(db, news_id)
            approved.append(news.id)
        except Exception:
            pass
    return success_response(message=f"通过 {len(approved)} 条")


@router.post("/news/batch-reject")
async def admin_batch_reject(
    ids: list[int],
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(db_config.get_db),
):
    rejected = []
    for news_id in ids:
        try:
            await crud_admin.admin_reject_news(db, news_id)
            rejected.append(news_id)
        except Exception:
            pass
    return success_response(message=f"驳回 {len(rejected)} 条")


@router.delete("/news/{news_id}/reject")
async def admin_reject_news_route(
    news_id: int,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(db_config.get_db),
):
    await crud_admin.admin_reject_news(db, news_id)
    return success_response(message="已驳回")


@router.put("/news/{news_id}")
async def admin_update_news_route(
    news_id: int,
    news_data: schemas_admin.AdminNewsUpdate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(db_config.get_db),
):
    news = await crud_admin.admin_update_news(db, news_id, news_data)
    return success_response(message="修改成功", data=schemas_admin.AdminNewsInfo.model_validate(news))


@router.delete("/news/{news_id}")
async def admin_delete_news_route(
    news_id: int,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(db_config.get_db),
):
    await crud_admin.admin_delete_news(db, news_id)
    return success_response(message="删除成功")


# ========== 分类管理 ==========
@router.get("/categories")
async def admin_list_categories(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(db_config.get_db),
):
    categories = await crud_admin.admin_get_categories(db)
    return success_response(
        message="获取成功",
        data=[schemas_admin.AdminCategoryInfo.model_validate(c) for c in categories],
    )


@router.post("/categories")
async def admin_create_category_route(
    cat_data: schemas_admin.AdminCategoryCreate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(db_config.get_db),
):
    cat = await crud_admin.admin_create_category(db, cat_data)
    return success_response(message="创建成功", data=schemas_admin.AdminCategoryInfo.model_validate(cat))


@router.put("/categories/{category_id}")
async def admin_update_category_route(
    category_id: int,
    cat_data: schemas_admin.AdminCategoryUpdate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(db_config.get_db),
):
    cat = await crud_admin.admin_update_category(db, category_id, cat_data)
    return success_response(message="修改成功", data=schemas_admin.AdminCategoryInfo.model_validate(cat))


@router.delete("/categories/{category_id}")
async def admin_delete_category_route(
    category_id: int,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(db_config.get_db),
):
    await crud_admin.admin_delete_category(db, category_id)
    return success_response(message="删除成功")
