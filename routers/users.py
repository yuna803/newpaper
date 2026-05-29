from fastapi import APIRouter, Depends, HTTPException
from crud import crud_users
from sqlalchemy.ext.asyncio import AsyncSession
from config import db_config
from crud.crud_users import authenticate_user
from models.model_users import User
from schemas import schemas_user
from schemas.schemas_user import UserAuth, userInfo,User_Update
from utils.response import success_response
from utils.auth import get_current_user

router=APIRouter(prefix="/api/user",tags=["users"])

#用户注册
@router.post("/register")
async def register(user_data: schemas_user.UserRequest,
                   db: AsyncSession = Depends(db_config.get_db)
                   ):

  existing_user = await crud_users.get_register(db,user_data.username)
  if existing_user:
    raise HTTPException(status_code=404, detail="用户已存在")

  user_return = await crud_users.create_username(db,user_data)
  token=await crud_users.create_token(db,user_return.id)

  data=UserAuth(token=token,user_info=userInfo.model_validate(user_return))
  return success_response(message="注册成功",data=data)

#登录
@router.post("/login")
async def login(user_data: schemas_user.UserRequest,
                   db: AsyncSession = Depends(db_config.get_db)
                   ):
  user=await authenticate_user(db,user_data.username,user_data.password)
  if not user:
      raise HTTPException(status_code=404,detail="用户名或密码错误")
  token=await crud_users.create_token(db,user.id)
  response=UserAuth(token=token,user_info=userInfo.model_validate(user))
  return success_response(message="登录成功",data=response)

#获取用户信息
@router.get("/info")
async def info(user:User =Depends(get_current_user)):
    return success_response(message="获取用户信息",data=userInfo.model_validate(user))

#修改用户数据
@router.put("/update")
async def put(user_data:User_Update,user:User =Depends(get_current_user),
              db: AsyncSession = Depends(db_config.get_db)):
    user=await crud_users.update_user(db,user_data,user.username)
    return success_response(message="修改成功",data=userInfo.model_validate(user))

#修改密码
@router.put("/password")
async def update_password(user_data: schemas_user.UserUpdatePassword,
                            user:User =Depends(get_current_user),
                            db: AsyncSession = Depends(db_config.get_db)):
    user=await crud_users.update_password(db,user_data,user.username)
    return success_response(message="修改成功",data=userInfo.model_validate(user)) 
