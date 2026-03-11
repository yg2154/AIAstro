from datetime import date
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# (month, day) ranges for each sign
_ZODIAC_RANGES = [
    ("Capricorn", (12, 22), (12, 31)),
    ("Capricorn", (1, 1), (1, 19)),
    ("Aquarius", (1, 20), (2, 18)),
    ("Pisces", (2, 19), (3, 20)),
    ("Aries", (3, 21), (4, 19)),
    ("Taurus", (4, 20), (5, 20)),
    ("Gemini", (5, 21), (6, 20)),
    ("Cancer", (6, 21), (7, 22)),
    ("Leo", (7, 23), (8, 22)),
    ("Virgo", (8, 23), (9, 22)),
    ("Libra", (9, 23), (10, 22)),
    ("Scorpio", (10, 23), (11, 21)),
    ("Sagittarius", (11, 22), (12, 21)),
]

_NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishtha",
    "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]


def get_zodiac_sign(birth_date: str) -> str:
    """Return zodiac sign for a YYYY-MM-DD birth date string."""
    try:
        d = date.fromisoformat(birth_date)
    except ValueError:
        raise ValueError(f"Invalid birth_date format: {birth_date!r}. Use YYYY-MM-DD.")

    month, day = d.month, d.day
    for sign, (sm, sd), (em, ed) in _ZODIAC_RANGES:
        if (month, day) >= (sm, sd) and (month, day) <= (em, ed):
            return sign

    # Should never reach here with valid dates
    raise ValueError(f"Could not determine zodiac for date: {birth_date}")


def get_nakshatra(birth_date: str, birth_time: Optional[str] = None, birth_place: Optional[str] = None) -> Optional[str]:
    """
    Compute nakshatra from Moon's ecliptic longitude using ephem.
    Returns None gracefully if birth_time is missing or ephem fails.
    """
    if not birth_time:
        return None
    try:
        import ephem

        # Parse date and time
        d = date.fromisoformat(birth_date)
        time_parts = birth_time.split(":")
        hour = int(time_parts[0])
        minute = int(time_parts[1]) if len(time_parts) > 1 else 0

        # Build ephem date string (UTC approximation — no timezone conversion for now)
        ephem_date_str = f"{d.year}/{d.month}/{d.day} {hour:02d}:{minute:02d}:00"

        moon = ephem.Moon()
        observer = ephem.Observer()
        observer.date = ephem_date_str
        # Default to approximate India coords if no place given
        observer.lat = "20.5937"
        observer.lon = "78.9629"
        moon.compute(observer)

        # Ecliptic longitude in degrees
        ecl = ephem.Ecliptic(moon, epoch=ephem.J2000)
        longitude = float(ecl.lon) * 180.0 / 3.141592653589793

        # Each nakshatra spans 360/27 ≈ 13.333 degrees
        index = int(longitude / (360.0 / 27)) % 27
        return _NAKSHATRAS[index]
    except Exception as exc:
        logger.warning("Nakshatra computation failed: %s", exc)
        return None
