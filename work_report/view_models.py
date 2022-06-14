from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, StrictInt, StrictStr, validator

from .database import models


class Category(BaseModel):
    name: StrictStr

    def __str__(self) -> str:
        return f"{self.name}"

    class Config:
        orm_mode = True


class Job(BaseModel):
    id: StrictInt
    name: StrictStr
    category: Category | None = None

    def __str__(self) -> str:
        if self.category is None:
            return f"#{self.id} {self.name}"
        return f"#{self.id} {self.category}/{self.name}"

    @validator("category", pre=True, allow_reuse=True)
    @classmethod
    def pony_set_category(cls, value: models.Category | None) -> Any:
        if value is None:
            return None
        return value.to_dict()

    class Config:
        orm_mode = True


class JobRecord(BaseModel):
    id: StrictInt
    job: Job
    start: datetime
    end: Optional[datetime]

    def __str__(self) -> str:
        datetime_format = "%H:%M"
        if self.end is None:
            return f"{self.start.strftime(datetime_format)} - ??:?? ({self.job})"
        return f"{self.start.strftime(datetime_format)} - {self.end.strftime(datetime_format)} ({self.job})"

    class Config:
        orm_mode = True


class Note(BaseModel):
    date: date
    content: StrictStr | None

    class Config:
        orm_mode = True
