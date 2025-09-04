import json
from datetime import datetime

import pytest
from faker import Faker

from fastgear.common.schema.custom_base_model_schema import CustomBaseModel


class DummyModel(CustomBaseModel):
    timestamp: datetime


@pytest.mark.describe("🧪 CustomBaseModel")
class TestCustomBaseModel:
    @pytest.mark.it("✅  Should serialize datetimes to ISO 8601 using model_dump_json")
    def test_datetime_serialization_to_isoformat_using_model_dump_json(self, faker: Faker) -> None:
        ts = faker.date_time()
        model = DummyModel(timestamp=ts)

        dumped_json = model.model_dump_json()
        data = json.loads(dumped_json)

        assert data["timestamp"] == ts.isoformat()

    @pytest.mark.it("✅  Should keep datetime objects when using model_dump (Python mode)")
    def test_model_dump_python_keeps_datetime_object(self, faker: Faker) -> None:
        ts = faker.date_time()
        model = DummyModel(timestamp=ts)

        data = model.model_dump()

        assert isinstance(data["timestamp"], datetime)
        assert data["timestamp"] == ts
