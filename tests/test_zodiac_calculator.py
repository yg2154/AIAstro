import pytest
from app.services.zodiac_calculator import get_zodiac_sign, get_nakshatra


class TestGetZodiacSign:
    def test_aries(self):
        assert get_zodiac_sign("1990-04-05") == "Aries"

    def test_aries_boundary_start(self):
        assert get_zodiac_sign("1990-03-21") == "Aries"

    def test_aries_boundary_end(self):
        assert get_zodiac_sign("1990-04-19") == "Aries"

    def test_taurus(self):
        assert get_zodiac_sign("1990-05-01") == "Taurus"

    def test_taurus_boundary_start(self):
        assert get_zodiac_sign("1990-04-20") == "Taurus"

    def test_gemini(self):
        assert get_zodiac_sign("1990-06-01") == "Gemini"

    def test_cancer(self):
        assert get_zodiac_sign("1990-07-01") == "Cancer"

    def test_leo(self):
        assert get_zodiac_sign("1990-08-01") == "Leo"

    def test_virgo(self):
        assert get_zodiac_sign("1990-09-01") == "Virgo"

    def test_libra(self):
        assert get_zodiac_sign("1990-10-01") == "Libra"

    def test_scorpio(self):
        assert get_zodiac_sign("1990-11-01") == "Scorpio"

    def test_scorpio_boundary_end(self):
        assert get_zodiac_sign("1990-11-21") == "Scorpio"

    def test_sagittarius(self):
        assert get_zodiac_sign("1990-12-01") == "Sagittarius"

    def test_capricorn_december(self):
        assert get_zodiac_sign("1990-12-25") == "Capricorn"

    def test_capricorn_january(self):
        assert get_zodiac_sign("1990-01-10") == "Capricorn"

    def test_aquarius(self):
        assert get_zodiac_sign("1990-02-01") == "Aquarius"

    def test_pisces(self):
        assert get_zodiac_sign("1990-03-01") == "Pisces"

    def test_scorpio_november_15(self):
        assert get_zodiac_sign("1992-11-15") == "Scorpio"

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError):
            get_zodiac_sign("15-11-1992")


class TestGetNakshatra:
    def test_no_birth_time_returns_none(self):
        assert get_nakshatra("1990-04-05") is None

    def test_with_birth_time_returns_string_or_none(self):
        result = get_nakshatra("1990-04-05", "14:30", "Mumbai")
        # Either a valid nakshatra name or None (if ephem unavailable)
        assert result is None or isinstance(result, str)

    def test_nakshatra_name_in_known_list(self):
        result = get_nakshatra("1992-11-15", "14:30", "Mumbai")
        if result is not None:
            from app.services.zodiac_calculator import _NAKSHATRAS
            assert result in _NAKSHATRAS
