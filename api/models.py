from sqlalchemy import BigInteger, Boolean, Column, Date, ForeignKey, Integer, String, Time, DateTime
from sqlalchemy.orm import relationship

from db.db_session import Base


class TimeSlot(Base):
    __tablename__ = "panel_timeslot"

    id = Column(Integer, primary_key=True)
    time = Column(Time, unique=True)

    def __repr__(self):
        return self.time.strftime("%H:%M")


class Appointment(Base):
    __tablename__ = "panel_appointment"

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime)
    date = Column(Date)
    time_slot_id = Column(Integer, ForeignKey("panel_timeslot.id"))
    bar_user_id = Column(Integer, ForeignKey("panel_baruser.id"))
    is_approved = Column(Boolean)
    # Связи с моделями TimeSlot, User
    time_slot = relationship("TimeSlot")
    bar_user = relationship("BarUser")


class BarUser(Base):
    __tablename__ = "panel_baruser"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=True)
    username = Column(String, nullable=True)
    name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    is_active = Column(Boolean)


class CustomDay(Base):
    __tablename__ = "panel_customday"

    id = Column(Integer, primary_key=True)
    date = Column(Date)
    day_type = Column(String)
