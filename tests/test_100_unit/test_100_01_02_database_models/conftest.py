import pytest

from work_report.database.database import DatabaseSingleton


@pytest.fixture(scope="function")
def fixt_init_db() -> None:
    db = DatabaseSingleton.get_instance()
    try:
        db.bind(provider="sqlite", filename=":memory:", create_db=True)
        db.generate_mapping(create_tables=True)
        yield db
    finally:
        db.drop_all_tables(with_all_data=True)
        db.provider = db.schema = None
