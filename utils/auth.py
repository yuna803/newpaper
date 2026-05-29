from fastapi import Header, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from crud import crud_users
from config.db_config import get_db


"""根据token查询用户"""
async def get_current_user(authorization: str = Header(..., alias="Authorization"),
                           db:AsyncSession=Depends(get_db),
):
    # 兼容 "Bearer xxx" 和直接传 token 两种格式
    token = authorization.split(" ")[-1]
    user=await crud_users.get_user_info(db,token)
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404,detail="令牌无效")
    return user