from __future__ import annotations

from pony.orm import Database


class InstantiationError(Exception):
    pass


class DatabaseSingleton(Database):  # type: ignore[misc]
    """Singleton inheriting from pony.orm.Database"""

    def __new__(cls) -> DatabaseSingleton:
        if hasattr(cls, "_singleton"):
            raise InstantiationError("This singleton has been already created")

        # Set private singleton property in order not to allow you to recreate instance
        cls._singleton: DatabaseSingleton = super().__new__(cls)

        return cls._singleton

    @classmethod
    def get_instance(cls) -> DatabaseSingleton:
        return cls._singleton


DatabaseSingleton()
