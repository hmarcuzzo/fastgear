from enum import Enum

import pytest

from fastgear.utils.enum_utils import EnumUtils


class TestEnum(Enum):
    TestValueOne = "test_value_one"
    TestValueTwo = "test_value_two"
    TestValueThree = "test_value_three"


@pytest.mark.describe("🧪  EnumUtils")
class TestEnumUtils:
    @pytest.mark.it("✅  Should convert camelCase to snake_case correctly")
    def test_camel_to_snake_basic_conversion(self):
        assert EnumUtils.camel_to_snake("CamelCase") == "camel_case"
        assert EnumUtils.camel_to_snake("HTTPRequest") == "http_request"
        assert EnumUtils.camel_to_snake("UserID") == "user_id"

    @pytest.mark.it("✅  Should handle numbers in camelCase to snake_case conversion")
    def test_camel_to_snake_with_numbers(self):
        assert EnumUtils.camel_to_snake("UserID123") == "user_id123"
        assert EnumUtils.camel_to_snake("Test123Value") == "test123_value"

    @pytest.mark.it("✅  Should handle single words in camelCase to snake_case conversion")
    def test_camel_to_snake_single_word(self):
        assert EnumUtils.camel_to_snake("test") == "test"
        assert EnumUtils.camel_to_snake("Test") == "test"

    @pytest.mark.it("✅  Should handle edge cases in camelCase to snake_case conversion")
    def test_camel_to_snake_edge_cases(self):
        assert EnumUtils.camel_to_snake("") == ""
        assert EnumUtils.camel_to_snake("already_snake_case") == "already_snake_case"

    @pytest.mark.it("✅  Should get correct object name for regular enum class")
    def test_get_object_name_regular_enum(self):
        assert EnumUtils.get_object_name(TestEnum) == "test_enum"

    @pytest.mark.it("✅  Should get correct object name for empty enum class")
    def test_get_object_name_empty_enum(self):
        class EmptyEnum(Enum):
            pass

        assert EnumUtils.get_object_name(EmptyEnum) == "empty_enum"

    @pytest.mark.it("✅  Should get correct object name for enum class with multiple words")
    def test_get_object_name_multiple_words(self):
        class MultipleWordEnum(Enum):
            pass

        assert EnumUtils.get_object_name(MultipleWordEnum) == "multiple_word_enum"
