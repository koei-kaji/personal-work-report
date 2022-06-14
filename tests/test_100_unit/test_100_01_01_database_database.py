import pytest

from work_report.database.database import DatabaseSingleton, InstantiationError


class TestDatabaseSingleton:
    def test_normal_same_instance(self) -> None:
        instance_1st = DatabaseSingleton.get_instance()
        instance_2nd = DatabaseSingleton.get_instance()
        assert id(instance_1st) == id(instance_2nd)

    def test_exc_instantiation_error(self) -> None:
        with pytest.raises(InstantiationError):
            DatabaseSingleton()
