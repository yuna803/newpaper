from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Index

from models.base import Base


class User_token(Base):
    __tablename__ = "user_token"

    __table_args__ = (
        Index('token_UNIQUE', 'token'),
        Index('fk_user_token_user_idx', 'user_id'),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="用户id")
    token: Mapped[str] = mapped_column(String(255), unique=True, comment="令牌")
    expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        comment="过期时间"
    )

    def __repr__(self):
        return f"<User_token(id={self.id},user_id={self.user_id}, token={self.token})>"


class User(Base):
    __tablename__ = "user"
    __table_args__ = (
        Index('fk_user_username_idx', 'username'),
        Index('idx_user_role', 'role'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="用户ID")
    username: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, comment="用户名")
    password: Mapped[str] = mapped_column(String(255), nullable=False, comment="密码")
    nickname: Mapped[str] = mapped_column(String(50), default="", comment="昵称")
    avatar: Mapped[Optional[str]] = mapped_column(String(255), default="", comment="用户头像")
    gender: Mapped[str] = mapped_column(String(10), default="unknown", comment="性别")
    bio: Mapped[str] = mapped_column(String(500), default="", comment="简介")
    phone: Mapped[str] = mapped_column(String(20), default="", comment="手机号")
    role: Mapped[str] = mapped_column(String(20), default="user", comment="角色: user/admin/disabled")
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        comment="更新时间"
    )

    def __repr__(self):
        return f"<User(id={self.id},username={self.username}, password={self.password}, nickname={self.nickname}, avatar={self.avatar}, gender={self.gender}, bio={self.bio}, phone={self.phone}, role={self.role})>"
