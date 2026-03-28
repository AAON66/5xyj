"""Tests for ID number masking utility."""

from backend.app.utils.masking import mask_id_number


class TestMaskIdNumber:
    def test_none_returns_none(self):
        assert mask_id_number(None) is None

    def test_empty_returns_empty(self):
        assert mask_id_number("") == ""

    def test_short_string_returned_as_is(self):
        assert mask_id_number("abc") == "abc"

    def test_seven_chars_returned_as_is(self):
        assert mask_id_number("1234567") == "1234567"

    def test_eight_chars_masked(self):
        # 8 chars: first 3 + 1 star + last 4 = "123*5678"
        assert mask_id_number("12345678") == "123*5678"

    def test_eighteen_char_id_number(self):
        # Standard 18-digit Chinese ID: first 3 + 11 stars + last 4
        result = mask_id_number("310105199001011234")
        assert result == "310***********1234"
        assert len(result) == 18

    def test_fifteen_char_id_number(self):
        # Old 15-digit format: first 3 + 8 stars + last 4
        result = mask_id_number("310105900101123")
        assert result == "310********1123"

    def test_preserves_non_numeric(self):
        # ID with X suffix
        result = mask_id_number("31010519900101123X")
        assert result == "310***********123X"
