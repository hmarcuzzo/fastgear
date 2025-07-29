import pytest

from fastgear.types.custom_enum import CustomEnum


class CustomEnumTest(CustomEnum):
    TestValueOne = "test_value_one"
    TestValueTwo = "test_value_two"


@pytest.mark.describe("🧪  CustomEnum")
class TestCustomEnumBehavior:
    @pytest.mark.it("✅  Should get correct object name for enum class")
    def test_object_name(self) -> None:
        assert CustomEnumTest.object_name() == "custom_enum_test"

    @pytest.mark.it("✅  Should get correct object name for enum class with multiple words")
    def test_object_name_multiple_words(self) -> None:
        class MultipleWordCustomEnum(CustomEnum):
            pass

        assert MultipleWordCustomEnum.object_name() == "multiple_word_custom_enum"

    @pytest.mark.it("✅  Should get correct object name for empty enum class")
    def test_object_name_empty_enum(self) -> None:
        class EmptyCustomEnum(CustomEnum):
            pass

        assert EmptyCustomEnum.object_name() == "empty_custom_enum"

    @pytest.mark.it("✅  Should get same object name when called from instance or class")
    def test_object_name_from_instance(self) -> None:
        enum_instance = CustomEnumTest.TestValueOne
        assert enum_instance.object_name() == CustomEnumTest.object_name()

    @pytest.mark.it("❌  Should fail when trying to get object name from non-enum class")
    def test_object_name_non_enum(self) -> None:
        class NonEnumClass:
            pass

        with pytest.raises(AttributeError):
            NonEnumClass.object_name()

    @pytest.mark.it("❌  Should fail when trying to get object name from regular Enum class")
    def test_object_name_regular_enum(self) -> None:
        from enum import Enum

        class RegularEnum(Enum):
            pass

        with pytest.raises(AttributeError):
            RegularEnum.object_name()
