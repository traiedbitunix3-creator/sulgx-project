from sqlalchemy import select

from database.models import User
from database.session import get_session_ctx


async def get_or_create_user(telegram_id: int, username: str | None, first_name: str | None) -> User:
    async with get_session_ctx() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if user is None:
            user = User(telegram_id=telegram_id, username=username, first_name=first_name)
            session.add(user)
            await session.flush()
        else:
            user.username = username or user.username
            user.first_name = first_name or user.first_name
        await session.refresh(user)
        return user


async def is_banned(telegram_id: int) -> bool:
    async with get_session_ctx() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        return bool(user and user.is_banned)


async def ban_user(telegram_id: int, banned: bool = True) -> bool:
    async with get_session_ctx() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if user is None:
            return False
        user.is_banned = banned
        return True


async def count_users() -> int:
    async with get_session_ctx() as session:
        result = await session.execute(select(User))
        return len(result.scalars().all())


async def all_user_ids() -> list[int]:
    async with get_session_ctx() as session:
        result = await session.execute(select(User.telegram_id).where(User.is_banned.is_(False)))
        return [row[0] for row in result.all()]
