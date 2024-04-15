from litestar import Litestar, get
from litestar.di import Provide
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import BarUser
from db.db_session import get_session


@get("/users")
async def get_active_users(session: AsyncSession):
    query_users = select(BarUser).filter(BarUser.is_active.is_(True))
    tmp_users = await session.execute(query_users)
    users = [[user.id, user.phone, user.name] for user in tmp_users.scalars().all()]
    return users


app = Litestar(route_handlers=[get_active_users], dependencies={"session": Provide(get_session)})
