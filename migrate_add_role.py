"""
数据库迁移脚本 - 添加 role 列并设置管理员

运行方式:
  python migrate_add_role.py

或将以下 SQL 语句手动在 MySQL 中执行:
  ALTER TABLE user ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'user' COMMENT '角色: user/admin/disabled';
  -- 将指定用户设为管理员 (替换 'admin_username' 为实际用户名)
  UPDATE user SET role = 'admin' WHERE username = 'admin';
  -- 修改 news 表的 content 列类型为 TEXT
  ALTER TABLE news MODIFY COLUMN content TEXT NOT NULL COMMENT '新闻内容';
  ALTER TABLE news MODIFY COLUMN description TEXT COMMENT '新闻描述';
"""
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

ASYNC_DATABASE_URL = "mysql+aiomysql://root:123456@localhost:3306/news_app?charset=utf8mb4"


async def migrate():
    engine = create_async_engine(ASYNC_DATABASE_URL)
    async with engine.begin() as conn:
        # 添加 role 列
        try:
            await conn.execute(text(
                "ALTER TABLE user ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'user' COMMENT '角色: user/admin/disabled'"
            ))
            print("[OK] role 列添加成功")
        except Exception as e:
            if "Duplicate column" in str(e):
                print("[SKIP] role 列已存在")
            else:
                print(f"[FAIL] role 列添加失败: {e}")

        # 修改新闻 content 和 description 列为 TEXT 类型
        try:
            await conn.execute(text(
                "ALTER TABLE news MODIFY COLUMN content TEXT NOT NULL COMMENT '新闻内容'"
            ))
            print("[OK] content 列改为 TEXT 成功")
        except Exception as e:
            print(f"[SKIP] content 列修改失败: {e}")

        try:
            await conn.execute(text(
                "ALTER TABLE news MODIFY COLUMN description TEXT COMMENT '新闻描述'"
            ))
            print("[OK] description 列改为 TEXT 成功")
        except Exception as e:
            print(f"[SKIP] description 列修改失败: {e}")

        # 检查 admin 用户
        result = await conn.execute(text("SELECT id, role FROM user WHERE username = 'admin'"))
        row = result.fetchone()
        if row is None:
            import bcrypt
            hashed = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()
            await conn.execute(text(
                "INSERT INTO user (username, password, nickname, role) VALUES ('admin', :pwd, '管理员', 'admin')"
            ), {"pwd": hashed})
            print("[OK] 默认管理员创建成功: admin / admin123")
        else:
            import bcrypt
            hashed = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()
            if row.role != 'admin':
                await conn.execute(text(
                    "UPDATE user SET password = :pwd, role = 'admin' WHERE username = 'admin'"
                ), {"pwd": hashed})
            else:
                await conn.execute(text(
                    "UPDATE user SET password = :pwd WHERE username = 'admin'"
                ), {"pwd": hashed})
            print("[OK] admin 密码已重置为: admin123")

    await engine.dispose()
    print("\n迁移完成!")


if __name__ == "__main__":
    asyncio.run(migrate())
