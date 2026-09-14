from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.security import TelegramAuthData
from database.models import User


async def get_or_create_user(session: AsyncSession, auth: TelegramAuthData) -> User:
    result = await session.execute(select(User).where(User.telegram_id == auth.user_id))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            telegram_id=auth.user_id,
            username=auth.username,
            first_name=auth.first_name,
        )
        session.add(user)
        await session.flush()
    else:
        user.username = auth.username or user.username
        user.first_name = auth.first_name or user.first_name

    return user
