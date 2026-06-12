from typing import Optional
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from sqlalchemy import text


class User:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory

    async def create_user(self, telegram_id: int, username: str, full_name: str) -> int:
        query = text("""
        INSERT INTO users (telegram_id, username, first_name)
        VALUES (:telegram_id, :username, :full_name)
        RETURNING id
        """)
        async with self.session_factory() as session:
            result = await session.execute(
                query,
                {"telegram_id": telegram_id, "username": username, "full_name": full_name}
            )
            await session.commit()
            return result.scalar_one()

    async def user_by_id(self, user_id: int) -> Optional[dict]:
        query = text("SELECT * FROM users WHERE id = :user_id")
        async with self.session_factory() as session:
            result = await session.execute(query, {"user_id": user_id})
            row = result.fetchone()
            return dict(row._mapping) if row else None

    async def user_by_telegram_id(self, telegram_id: int) -> Optional[dict]:
        query = text("SELECT * FROM users WHERE telegram_id = :telegram_id")
        async with self.session_factory() as session:
            result = await session.execute(query, {"telegram_id": telegram_id})
            row = result.fetchone()
            return dict(row._mapping) if row else None

    async def update_user(self, user_id: int, username: str, full_name: str):
        query = text("""
        UPDATE users
        SET username = :username, name = :full_name
        WHERE id = :user_id
        """)
        async with self.session_factory() as session:
            await session.execute(
                query,
                {"username": username, "full_name": full_name, "user_id": user_id}
            )
            await session.commit()

    async def delete_user(self, user_id: int):
        query = text("DELETE FROM users WHERE id = :user_id")
        async with self.session_factory() as session:
            await session.execute(query, {"user_id": user_id})
            await session.commit()
