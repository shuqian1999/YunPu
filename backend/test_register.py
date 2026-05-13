import asyncio
import sys
import os
sys.path.append(os.path.dirname(__file__))

from app.core.database import async_session
from app.services.user import UserService
from app.schemas.user import UserCreate

async def test_register():
    async with async_session() as db:
        user_in = UserCreate(username="testuser", email="test@example.com", password="testpass123")
        try:
            user = await UserService.create(db, user_in)
            print(f"User created: {user.username}, id: {user.id}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_register())