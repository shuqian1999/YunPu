from typing import Any, Dict, Optional, Union

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.schemas.user import UserCreate


class UserService:
    @staticmethod
    async def get_by_username(db: AsyncSession, username: str) -> Optional[User]:
        result = await db.execute(select(User).where(User.username == username))
        return result.scalars().first()

    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
        return await db.get(User, user_id)

    @staticmethod
    async def create(db: AsyncSession, obj_in: UserCreate) -> User:
        print(f"Creating user: {obj_in.username}")
        try:
            db_obj = User(
                username=obj_in.username,
                password_hash=get_password_hash(obj_in.password),
            )
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            print(f"User created with id: {db_obj.id}")
            return db_obj
        except Exception as e:
            print(f"Error creating user: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def authenticate(db: AsyncSession, username: str, password: str) -> Optional[User]:
        user = await UserService.get_by_username(db, username)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user
