"""
数据库迁移脚本 - 添加 role、status、source_url 列，创建默认管理员

使用方法:
  1. 修改下方 DATABASE_URL 为你的实际数据库连接信息
  2. 重命名为 migrate_add_role.py
  3. 运行: python migrate_add_role.py
"""
import asyncio
import bcrypt
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# 修改为你的数据库连接信息
DATABASE_URL = "mysql+aiomysql://用户名:密码@localhost:3306/数据库名?charset=utf8mb4"


async def migrate():
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        # 添加 role 列
        try:
            await conn.execute(text(
                "ALTER TABLE user ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'user' COMMENT '角色: user/admin/disabled'"
            ))
            print("[OK] role 列添加成功")
        except Exception as e:
            if "Duplicate" in str(e):
                print("[SKIP] role 列已存在")
            else:
                print(f"[FAIL] role 列添加失败: {e}")

        # 添加 status 列
        try:
            await conn.execute(text(
                "ALTER TABLE news ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'published' COMMENT '状态: draft/published'"
            ))
            print("[OK] status 列添加成功")
        except Exception as e:
            if "Duplicate" in str(e):
                print("[SKIP] status 列已存在")
            else:
                print(f"[FAIL] status 列添加失败: {e}")

        # 添加 source_url 列
        try:
            await conn.execute(text(
                "ALTER TABLE news ADD COLUMN source_url VARCHAR(500) DEFAULT NULL COMMENT '来源URL，用于去重'"
            ))
            print("[OK] source_url 列添加成功")
        except Exception as e:
            if "Duplicate" in str(e):
                print("[SKIP] source_url 列已存在")
            else:
                print(f"[FAIL] source_url 列添加失败: {e}")

        # 修改 content 列为 TEXT
        try:
            await conn.execute(text("ALTER TABLE news MODIFY COLUMN content TEXT NOT NULL COMMENT '新闻内容'"))
            await conn.execute(text("ALTER TABLE news MODIFY COLUMN description TEXT COMMENT '新闻描述'"))
            print("[OK] content/description 列改为 TEXT 成功")
        except Exception as e:
            print(f"[SKIP] 列修改失败: {e}")

        # 创建默认管理员
        result = await conn.execute(text("SELECT COUNT(*) FROM user WHERE username = 'admin'"))
        count = result.scalar()
        if count == 0:
            hashed = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()
            await conn.execute(text(
                "INSERT INTO user (username, password, nickname, role) VALUES ('admin', :pwd, '管理员', 'admin')"
            ), {"pwd": hashed})
            print("[OK] 默认管理员创建成功: admin / admin123")
        else:
            hashed = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()
            await conn.execute(text("UPDATE user SET password = :pwd WHERE username = 'admin'"), {"pwd": hashed})
            print("[OK] admin 密码已重置为: admin123")

    await engine.dispose()
    print("\n迁移完成!")


if __name__ == "__main__":
    asyncio.run(migrate())
