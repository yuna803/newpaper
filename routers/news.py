from fastapi import APIRouter, Depends, HTTPException
from fastapi.params import Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from config import db_config
from crud import crud_news
router=APIRouter(prefix="/api/news",tags=["new"])


# 接口实现流程
# 1.模块化路由 → API 接口规范文档
# 2.定义模型类 →数据库表(数据库设计文档)
# 3.在crud文件夹里面创建文件，封装操作数据库的方法
# 4.在路由处理函数里面调用 crud 封装好的方法，响应结果

@router.get("/categories")
async def get_categories(skip: int = 0, limit: int = 100,db:AsyncSession=Depends(db_config.get_db)):
    categorise=await crud_news.get_categories(db,skip,limit)
    return {
  "code": 200,
  "message": "success",
  "data": categorise
}


@router.get("/list")
async def get_news_list(categoryId: int = Query(...,alias="categoryId"),
                        page: int = Query(1,alias="page"),
                        pageSize: int = Query(10,alias="pageSize",le=100),#le是小于等于
                        db:AsyncSession=Depends(db_config.get_db)
                        ):

#处理分页逻辑 ->查询新闻列表 ->计算总量 ->
    offset=(page-1)*pageSize #计算偏移量
    news_ls=await crud_news.get_news_list(db,categoryId,offset,pageSize)#新闻列表
    total=await crud_news.get_news_count(db,categoryId) #全部新闻数量
    has_more=total>offset+len(news_ls)
    return{
  "code": 200,
  "message": "success",
  "data": {
    "list": news_ls,
    "total": total,
    "hasMore": has_more
  }
}

@router.get("/detail")
async def get_news_detail(id: int=Query(...,alias="id"),db:AsyncSession=Depends(db_config.get_db)):
    news=await crud_news.get_news_detail(db,id)
    if not news:
        raise HTTPException (status_code=404,detail="新闻不存在")
    get_news_list = await crud_news.detail_relatedNews(
        db,
        news.category_id,
        news.id,
        pageSize=5
    )
    return{
      "code": 200,
      "message": "success",
      "data": {
        "id": news.id,
        "title": news.title,
        "content": news.content,
        "image": "null",
        "author": news.author,
        "publishTime": news.publish_time,
        "categoryId": news.category_id,
        "views": news.views,
        "relatedNews": get_news_list
      }
    }






