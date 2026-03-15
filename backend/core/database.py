import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = (
    f"postgresql+asyncpg://"
    f"{os.environ.get('POSTGRES_USER', 'climarisk')}:"
    f"{os.environ.get('POSTGRES_PASSWORD', 'climarisk')}@"
    f"{os.environ.get('POSTGRES_HOST', 'postgres')}:"
    f"{os.environ.get('POSTGRES_PORT', '5432')}/"
    f"{os.environ.get('POSTGRES_DB', 'climarisk')}"
)

engine = create_async_engine(DATABASE_URL, echo=False)


AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

SessionLocal = AsyncSessionLocal


class Base(DeclarativeBase):
    pass


async def get_db():
    async with SessionLocal() as session:
        yield session