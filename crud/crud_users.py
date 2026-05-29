from datetime import datetime, timedelta
import uuid
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from utils import securit
from models.model_users import User,User_token
from schemas import schemas_user
from fastapi import HTTPException

#查询 用户名是否存在
async def get_register(db:AsyncSession,username: str):
    stmt = select(User).where(User.username == username)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


#创建用户
async def create_username(db:AsyncSession,schema: schemas_user.UserRequest):
    hasher_password = securit.get_hash_password(schema.password)
    user=User(username=schema.username,password=hasher_password)
    db.add(user)
    await db.commit()
    await db.refresh(user)#读取最新的数据
    return user

#生成令牌
async def create_token(db:AsyncSession,user_id: int):
    # 生成令牌 +设置令牌有效期 ->查询数据库是否存在该用户 ->不存在则创建,存在则更新
    token=str(uuid.uuid4())
    expire_time= datetime.now() + timedelta(days=7)
    stmt = select(User_token).where(User_token.user_id == user_id)
    result = await db.execute(stmt)
    user_token_return = result.scalar_one_or_none()
    if user_token_return:
        user_token_return.token=token
        user_token_return.expires_at=expire_time
    else:
        user_token = User_token(user_id=user_id, token=token, expires_at=expire_time)
        db.add(user_token)

    await db.commit()
    return token

#用户认证
async def authenticate_user (db:AsyncSession,username: str,password: str):
    user=await get_register(db,username)
    # 用户不存在
    if not user:
        return None
    # 验证密码
    if not securit.verify_password(password,user.password):
        return None

    return user

#查询用户信息
async def get_user_info(db: AsyncSession, token: str):
    # 1. 先查 token 表（拿 User_token 对象）
    query = select(User_token).where(User_token.token == token)
    result = await db.execute(query)
    db_token = result.scalar_one_or_none()

    # 2. 判断 token 是否存在 / 过期
    if not db_token or db_token.expires_at < datetime.now():
        return None

    # 3. 再查用户
    query_user = select(User).where(User.id == db_token.user_id)
    result_user = await db.execute(query_user)
    return result_user.scalar_one_or_none()

#修改用户信息
async def update_user(db:AsyncSession,user_data: schemas_user.User_Update,username: str):
    query=update(User).where(User.username == username).values(**user_data.model_dump(
        exclude_unset=True,
        exclude_none=True
    ))
    result=await db.execute(query)
    await db.commit()
    #检查更新行数
    if result.rowcount==0:
        raise HTTPException(status_code=404,detail="用户不存在")
    updated_user=await get_register(db,username)
    return updated_user

#修改用户密码
async def update_password(db:AsyncSession,user_data: schemas_user.UserUpdatePassword,username: str):
    # 查询用户是否存在
    user=await get_register(db,username)
    if not user:
        raise HTTPException(status_code=404,detail="用户不存在")
    # 验证旧密码
    if not securit.verify_password(user_data.old_password,user.password):
        raise HTTPException(status_code=400,detail="旧密码错误")
    # 更新新密码
    user.password = securit.get_hash_password(user_data.new_password)
    await db.commit()
    return user