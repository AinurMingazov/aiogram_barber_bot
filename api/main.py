from litestar import Litestar, get
from litestar.di import Provide
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import BarUser
from api.schemas import BarUserSchema
from db.db_session import get_session


@get("/users")
async def get_active_users(session: AsyncSession) -> list[BarUserSchema]:
    query_users = select(BarUser).filter(BarUser.is_active.is_(True))
    tmp_users = await session.execute(query_users)
    users = [BarUserSchema(id=user.id, user_id=user.user_id, username=user.username,
                           name=user.name, phone=user.phone, is_active=user.is_active)
             for user in tmp_users.scalars().all()]
    return users


app = Litestar(route_handlers=[get_active_users], dependencies={"session": Provide(get_session)})
