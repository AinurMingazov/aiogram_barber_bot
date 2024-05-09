from datetime import time
from typing import Optional

from pydantic import BaseModel


class BarUserSchema(BaseModel):
    id: int
    user_id: Optional[int]
    username: Optional[str]
    name: Optional[str]
    phone: Optional[str]
    is_active: bool


class TimeSlotSchema(BaseModel):
    id: int
    time: time
