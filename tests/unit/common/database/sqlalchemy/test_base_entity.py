from datetime import datetime, timedelta

import pytest

from fastgear.common.database.sqlalchemy.base_entity import (
    BaseEntity,
    set_before_insert,
    set_before_update,
)


@pytest.mark.describe("🧪  BaseEntity")
class TestBaseEntity:
    @pytest.mark.it("✅  Should generate snake_case __tablename__ from CamelCase class name")
    def test_tablename_generation(self):
        class MyTestEntity(BaseEntity):
            pass

        class User(BaseEntity):
            pass

        class UserProfile(BaseEntity):
            pass

        assert MyTestEntity.__tablename__ == "my_test_entity"
        assert User.__tablename__ == "user"
        assert UserProfile.__tablename__ == "user_profile"

    @pytest.mark.it("✅  set_before_insert should set created_at and updated_at when missing")
    def test_set_before_insert_sets_timestamps(self):
        class FakeTarget:
            created_at = None
            updated_at = None

        target = FakeTarget()
        set_before_insert(None, None, target)

        assert isinstance(target.created_at, datetime)
        assert isinstance(target.updated_at, datetime)
        assert target.updated_at == target.created_at

    @pytest.mark.it("✅  __init__ should forward kwargs to Base via super().__init__")
    def test_init_forwards_kwargs_to_super(self):
        class KwEntity(BaseEntity):
            pass

        # passing a known mapped kwarg (created_at) should be accepted and set by the declarative constructor
        now = datetime.now()
        e = KwEntity(created_at=now)
        assert hasattr(e, "created_at")
        assert e.created_at == now

    @pytest.mark.it(
        "✅  set_before_insert should set updated_at to created_at when updated_at is older"
    )
    def test_set_before_insert_updates_updated_when_older(self):
        class FakeTarget:
            pass

        now = datetime.now()
        earlier = now - timedelta(days=1)

        target = FakeTarget()
        target.created_at = now
        target.updated_at = earlier

        set_before_insert(None, None, target)

        assert target.updated_at == target.created_at

    @pytest.mark.it("✅  set_before_insert should set updated_at when it's None")
    def test_set_before_insert_sets_updated_when_none(self):
        class FakeTarget:
            pass

        now = datetime.now()

        target = FakeTarget()
        target.created_at = now
        target.updated_at = None

        set_before_insert(None, None, target)

        assert target.updated_at == target.created_at

    @pytest.mark.it("✅  set_before_update should overwrite updated_at with current time")
    def test_set_before_update_sets_updated(self):
        class FakeTarget:
            pass

        old = datetime(2000, 1, 1)  # noqa: DTZ001
        target = FakeTarget()
        target.updated_at = old

        set_before_update(None, None, target)

        assert isinstance(target.updated_at, datetime)
        assert target.updated_at > old
