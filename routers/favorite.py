from fastapi import APIRouter,Depends
from fastapi import Depends,Query
from sqlalchemy.ext.asyncio import AsyncSession
from models.model_users import User
from utils.response import success_response
from config import db_config
from crud import crud_users,crud_favorites
from utils.auth import get_current_user
from models.models_favorit import Favorite
from schemas.schemas_favorite import FavoriteBase

router=APIRouter(prefix="/api/favorite",tags=["favorite"])
#检查新闻收藏状态
@router.get("/check")
async def check_favorite(newsId: int = Query(...,alias="newsId"),
                        user:User =Depends(get_current_user),
                        db: AsyncSession = Depends(db_config.get_db)):
    favorite=await crud_favorites.get_favorite(db,user.id,newsId)
    if favorite:
        return success_response(message="已收藏",data=favorite)
    else:
        return success_response(message="未收藏",data=None)
    
#添加新闻收藏
@router.post("/add")
async def add_favorite(favorite_data: FavoriteBase,
                      user:User =Depends(get_current_user),
                      db: AsyncSession = Depends(db_config.get_db)):
    favorite=await crud_favorites.get_favorite(db,user.id,favorite_data.news_id)
    if favorite:
        return success_response(message="已收藏",data=favorite)
    new_favorite=await crud_favorites.add_favorite(db,user.id,favorite_data.news_id)
    return success_response(message="收藏成功",data=new_favorite)


#收藏列表
@router.get("/list")
async def list_favorites(page: int = Query(1, ge=1), 
                         pageSize: int = Query(10, ge=1, le=100),
                         user:User =Depends(get_current_user),
                        db: AsyncSession = Depends(db_config.get_db)):
    result,total=await crud_favorites.list_favorites(db,user.id,page,pageSize)
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
        "favoriteTime": favorite.created_at,
        "favoriteId": favorite.id
    }
        list_data.append(item)
    has_more = (page * pageSize) < total
    return success_response(message="收藏列表",data={
            "list": list_data,
            "total": total,
            "hasMore": has_more
        })

#取消新闻收藏
@router.delete("/remove")
async def remove_favorite(newsId: int = Query(...,alias="newsId"),
                        user:User =Depends(get_current_user),
                        db: AsyncSession = Depends(db_config.get_db)):
    favorite=await crud_favorites.get_favorite(db,user.id,newsId)
    if favorite:
        await crud_favorites.remove_favorite(db,user.id,newsId)
        return success_response(message="取消收藏成功",data=None)
    return success_response(message="未收藏",data=None)

#清空收藏
@router.delete("/clear")
async def clear_favorites(user:User =Depends(get_current_user),
                        db: AsyncSession = Depends(db_config.get_db)):
    i=await crud_favorites.clear_favorites(db,user.id)
    return success_response(
        message=f"成功删除{i}条收藏记录",
        data=await crud_favorites.list_favorites(db,user.id)
        )