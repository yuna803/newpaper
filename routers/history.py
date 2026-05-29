from routers.users import get_current_user
from config import db_config
from fastapi import Depends,Query
from models.model_users import User
from fastapi import APIRouter
from schemas import schemas_history
from sqlalchemy.ext.asyncio import AsyncSession
from crud import crud_history
from utils.response import success_response

router=APIRouter(prefix="/api/history",tags=["history"])

@router.post("/add")
async def add_history(history_data: schemas_history.HistoryBase,
                      user:User =Depends(get_current_user),
                      db: AsyncSession = Depends(db_config.get_db)):
    history=await crud_history.add_history(db,user.id,history_data.news_id)
    return success_response(message="添加成功",data=history)

@router.get("/list")
async def list_history(page: int = Query(1, ge=1), 
                         pageSize: int = Query(10, ge=1, le=100),
                         user:User =Depends(get_current_user),
                        db: AsyncSession = Depends(db_config.get_db)):
    result,total=await crud_history.list_history(db,user.id,page,pageSize)
    list_data = []
    for favorite, news  in result:
        item = {
        "id": news.id,
        "title": news.title,
        "description": news.description,
        "image": news.image,
        "author": news.author,
        "publishTime": news.publish_time,
        "categoryId": news.category_id,
        "views": news.views,
        "favoriteTime": favorite.view_time,
        "favoriteId": favorite.id
    }
        list_data.append(item)
    has_more = (page * pageSize) < total
    return success_response(message="收藏列表",data={
            "list": list_data,
            "total": total,
            "hasMore": has_more
        })


@router.delete("/delete")
async def remove_favorite(newsId: int = Query(...,alias="newsId"),
                      user:User =Depends(get_current_user),
                      db: AsyncSession = Depends(db_config.get_db)):
    favorite=await crud_history.remove_history(db,user.id,newsId)
    return success_response(message="删除成功",data=favorite)

@router.delete("/clear")
async def clear_favorites(user:User =Depends(get_current_user),
                      db: AsyncSession = Depends(db_config.get_db)):
    await crud_history.clear_history(db,user.id)
    return success_response(message="清空成功",data=None)