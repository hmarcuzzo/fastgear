import re

import pytest

from fastgear.constants.regex_expressions import ANY_CHAR, OPERATOR, ORDER_BY_QUERY


@pytest.mark.describe("🧪  Regex Expressions")
class TestRegexExpressions:
    @pytest.mark.it("✅ Should validate ORDER_BY_QUERY regex correctly")
    @pytest.mark.parametrize("query", ["ASC", "DESC"])
    def test_order_by_query_correct(self, query: str) -> None:
        assert re.match(ORDER_BY_QUERY, query)

    @pytest.mark.it("❌ Should invalidate incorrect ORDER_BY_QUERY inputs")
    @pytest.mark.parametrize("query", ["RANDOM", "INVALID"])
    def test_order_by_query_incorrect(self, query: str) -> None:
        assert not re.match(ORDER_BY_QUERY, query)

    @pytest.mark.it("✅ Should validate ANY_CHAR regex correctly")
    @pytest.mark.parametrize("query", ["abc", "123", "A1B2C3", "valid_name_123"])
    def test_any_char_correct(self, query: str) -> None:
        assert re.match(ANY_CHAR, query)

    @pytest.mark.it("❌ Should invalidate incorrect ANY_CHAR inputs")
    @pytest.mark.parametrize("query", ["", "!@#", "\n"])
    def test_any_char_incorrect(self, query: str) -> None:
        assert not re.match(ANY_CHAR, query)

    @pytest.mark.it("✅ Should validate OPERATOR regex correctly")
    @pytest.mark.parametrize("query", ["AND", "OR"])
    def test_operator_correct(self, query: str) -> None:
        assert re.match(OPERATOR, query)

    @pytest.mark.it("❌ Should invalidate incorrect OPERATOR inputs")
    @pytest.mark.parametrize("query", ["NOT", "XOR", "&&"])
    def test_operator_incorrect(self, query: str) -> None:
        assert not re.match(OPERATOR, query)
