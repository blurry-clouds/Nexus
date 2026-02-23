from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Memory, ModLog, User


async def get_or_create_user(
    session: AsyncSession,
    user_id: int,
    username: str,
) -> User:
    user = await session.get(User, user_id)
    if user:
        if user.username != username:
            user.username = username
        user.last_seen = datetime.utcnow()
        await session.commit()
        await session.refresh(user)
        return user

    user = User(
        id=user_id,
        username=username,
        trust_score=100,
        preferred_games=[],
        warning_count=0,
        last_seen=datetime.utcnow(),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def upsert_user_memory(
    session: AsyncSession,
    user_id: int,
    key: str,
    value: str,
) -> Memory:
    stmt = select(Memory).where(Memory.user_id == user_id, Memory.key == key)
    result = await session.execute(stmt)
    memory = result.scalar_one_or_none()

    if memory:
        memory.value = value
        memory.updated_at = datetime.utcnow()
    else:
        memory = Memory(user_id=user_id, key=key, value=value)
        session.add(memory)

    await session.commit()
    await session.refresh(memory)
    return memory


async def get_user_memories(session: AsyncSession, user_id: int) -> list[Memory]:
    stmt = select(Memory).where(Memory.user_id == user_id).order_by(Memory.updated_at.desc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def add_mod_log(
    session: AsyncSession,
    user_id: int,
    action: str,
    reason: str,
    confidence: int,
    message_content: str,
    channel_id: int,
    mod_override: bool = False,
) -> ModLog:
    row = ModLog(
        user_id=user_id,
        action=action,
        reason=reason,
        confidence=confidence,
        message_content=message_content,
        channel_id=channel_id,
        mod_override=mod_override,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row
