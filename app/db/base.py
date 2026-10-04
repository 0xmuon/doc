"""base class.all models come from this only."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
