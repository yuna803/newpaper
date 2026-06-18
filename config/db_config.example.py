from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine

# 数据库URL - 替换为你的实际配置
ASYNC_DATABASE_URL = "mysql+aiomysql://用户名:密码@主机:端口/数据库名?charset=utf8mb4"

async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=True,
    pool_size=10,
    max_overflow=20
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
