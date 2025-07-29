import pytest
from faker import Faker

from fastgear.common.schema import DetailResponseSchema
from fastgear.utils.json_utils import JsonUtils


class DetailResponseFixture(DetailResponseSchema):
    loc: list[str] = ["test"]
    msg: str = "Test message"
    type: str = "test_type"


@pytest.mark.describe("🧪  JsonUtils")
class TestJsonUtils:
    @pytest.fixture
    def faker(self) -> Faker:
        return Faker()

    @pytest.mark.it("✅  Should serialize datetime objects to ISO format")
    def test_json_serial_datetime(self, faker: Faker):
        test_datetime = faker.date_time()
        result = JsonUtils.json_serial(test_datetime)
        assert result == test_datetime.isoformat()

    @pytest.mark.it("✅  Should serialize date objects to ISO format")
    def test_json_serial_date(self, faker: Faker):
        test_date = faker.date_object()
        result = JsonUtils.json_serial(test_date)
        assert result == test_date.isoformat()

    @pytest.mark.it("✅  Should serialize DetailResponseSchema objects to dict")
    def test_json_serial_detail_response(self, faker: Faker):
        test_response = DetailResponseFixture(
            loc=[faker.word()], msg=faker.sentence(), type=faker.word()
        )
        result = JsonUtils.json_serial(test_response)
        assert isinstance(result, dict)
        assert result["loc"] == test_response.loc
        assert result["msg"] == test_response.msg
        assert result["type"] == test_response.type

    @pytest.mark.it("❌  Should raise TypeError for non-serializable objects")
    def test_json_serial_unsupported_type(self):
        with pytest.raises(TypeError) as exc_info:
            JsonUtils.json_serial(object())
        assert "Type <class 'object'> not serializable" in str(exc_info.value)
