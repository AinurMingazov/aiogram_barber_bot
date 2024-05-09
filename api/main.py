from apscheduler.schedulers.asyncio import AsyncIOScheduler
from litestar import Litestar, get
from litestar.di import Provide
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import BarUser
from api.schemas import BarUserSchema
from api.tasks import send_one_hour_behind_appointment, send_two_weeks_after_appointment
from db.db_session import get_session


async def init_scheduler(app: Litestar) -> None:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_one_hour_behind_appointment, "cron", minute="01")
    scheduler.add_job(send_two_weeks_after_appointment, "cron", hour="08", minute="00")
    scheduler.start()
    app.state.scheduler = scheduler


@get("/users")
async def get_active_users(session: AsyncSession) -> list[BarUserSchema]:
    query_users = select(BarUser).filter(BarUser.is_active.is_(True))
    tmp_users = await session.execute(query_users)
    users = [
        BarUserSchema(
            id=user.id,
            user_id=user.user_id,
            username=user.username,
            name=user.name,
            phone=user.phone,
            is_active=user.is_active,
        )
        for user in tmp_users.scalars().all()
    ]
    return users


app = Litestar(
    on_startup=[init_scheduler], route_handlers=[get_active_users], dependencies={"session": Provide(get_session)}
)
