from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class UserRequest(BaseModel):
    username: str
    password: str

class User_InfoBase(BaseModel):
    """注册"""
    nickname: Optional[str]=Field( None, description="昵称"),
    avatar:  Optional[str]=Field(None,description="用户头像"),
    gender: Optional[str]=Field(None,description="性别"),
    bio: Optional[str]=Field(None,description="简介"),

class userInfo(User_InfoBase):
    id: int
    username: str
    role: Optional[str] = None
    model_config = ConfigDict(
        from_attributes=True  # 将orm模型属性映射为pydantic模型属性
    )

class UserAuth(BaseModel):
    token:str
    user_info:userInfo=Field(...,alias="userInfo")

    model_config = ConfigDict(
        populate_by_name=True,# 通过字段名兼容
        from_attributes= True # 将orm模型属性映射为pydantic模型属性
    )

class User_Update(BaseModel):
    nickname: str=None
    avatar: str=None
    gender: str=None
    bio: str=None
    phone: str=None

class UserUpdatePassword(BaseModel):
    old_password: str
    new_password: str
