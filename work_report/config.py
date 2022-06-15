from typing import Any, Dict

from pydantic import BaseSettings


class DatabaseSettings(BaseSettings):
    # NOTE: https://docs.ponyorm.org/api_reference.html?highlight=create_db#supported-databases
    provider: str = "sqlite"
    filename: str = "../sqlite.db"
    create_db: bool = True
    create_tables: bool = True

    def dict_bind(self) -> Dict[str, Any]:
        return self.dict(include={"provider", "filename", "create_db"})
