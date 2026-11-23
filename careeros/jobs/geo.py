"""Where a job is, or who may take it if it's remote, against the countries a user targets.

Shared by scoring (a location factor) and the decision criteria shown in the reader.
"""

import re
from typing import Iterable, Optional

COUNTRY_NAMES = [
    ("United States", "US"), ("Canada", "CA"), ("Mexico", "MX"),
    ("Germany", "DE"), ("United Kingdom", "GB"), ("France", "FR"),
    ("Netherlands", "NL"), ("Switzerland", "CH"), ("Sweden", "SE"),
    ("Norway", "NO"), ("Denmark", "DK"), ("Finland", "FI"), ("Spain", "ES"),
    ("Portugal", "PT"), ("Italy", "IT"), ("Poland", "PL"), ("Austria", "AT"),
    ("Belgium", "BE"), ("Ireland", "IE"), ("Czech Republic", "CZ"), ("Czechia", "CZ"),
    ("Estonia", "EE"), ("Latvia", "LV"), ("Lithuania", "LT"), ("Romania", "RO"), ("Bulgaria", "BG"),
    ("Hungary", "HU"), ("Greece", "GR"), ("Croatia", "HR"), ("Slovenia", "SI"), ("Slovakia", "SK"),
    ("Serbia", "RS"), ("Ukraine", "UA"), ("Cyprus", "CY"), ("Malta", "MT"), ("Luxembourg", "LU"),
    ("United Arab Emirates", "AE"), ("Saudi Arabia", "SA"), ("Turkey", "TR"), ("Türkiye", "TR"),
    ("Israel", "IL"), ("Qatar", "QA"), ("Uzbekistan", "UZ"), ("Kazakhstan", "KZ"),
    ("Azerbaijan", "AZ"), ("Georgia", "GE"), ("Singapore", "SG"), ("Japan", "JP"),
    ("South Korea", "KR"), ("Australia", "AU"), ("New Zealand", "NZ"),
    ("India", "IN"), ("China", "CN"), ("Hong Kong", "HK"), ("Taiwan", "TW"),
    ("Vietnam", "VN"), ("Indonesia", "ID"), ("Thailand", "TH"), ("Malaysia", "MY"),
    ("Philippines", "PH"), ("Brazil", "BR"), ("Argentina", "AR"),
    ("Colombia", "CO"), ("Chile", "CL"), ("South Africa", "ZA"),
    ("Nigeria", "NG"), ("Kenya", "KE"), ("Egypt", "EG"),
]
# Cities that usually appear without their country
CITIES = {
    "london": "GB", "manchester": "GB", "edinburgh": "GB", "cambridge, uk": "GB",
    "berlin": "DE", "munich": "DE", "münchen": "DE", "hamburg": "DE", "frankfurt": "DE", "cologne": "DE", "köln": "DE",
    "zurich": "CH", "zürich": "CH", "geneva": "CH", "basel": "CH", "lausanne": "CH",
    "madrid": "ES", "barcelona": "ES", "valencia": "ES", "paris": "FR", "amsterdam": "NL", "dublin": "IE",
    "lisbon": "PT", "warsaw": "PL", "krakow": "PL", "vienna": "AT", "stockholm": "SE", "helsinki": "FI",
    "istanbul": "TR", "i̇stanbul": "TR", "ankara": "TR", "izmir": "TR", "dubai": "AE",
    "new york": "US", "san francisco": "US", "seattle": "US", "toronto": "CA",
}
EUROPE = {"DE", "GB", "FR", "NL", "CH", "SE", "NO", "DK", "FI", "ES", "PT", "IT", "PL", "AT", "BE", "IE", "CZ",
          "EE", "LV", "LT", "RO", "BG", "HU", "GR", "HR", "SI", "SK", "RS", "UA", "CY", "MT", "LU"}
EMEA = EUROPE | {"TR", "AE", "SA", "IL", "QA", "EG", "ZA", "NG", "KE", "GE", "AZ"}
_US_STATE = re.compile(r",\s*(CA|NY|TX|WA|MA|IL|CO|GA|NC|VA|AZ|FL|OH|PA|OR|UT|NV)\b")
_OPEN_TO = re.compile(r"Open to candidates in:\s*([^.\n]+)", re.I)
_ANYWHERE = ("worldwide", "global", "anywhere", "any country", "fully remote, any")


def countries_in(text: Optional[str]) -> list[tuple[str, str]]:
    """Every (code, name) named in a location string, in order, without repeats."""
    if not text or text == "Unknown":
        return []
    lo = text.lower()
    found: dict[str, str] = {}
    for name, code in COUNTRY_NAMES:
        if name.lower() in lo:
            found.setdefault(code, name)
    for city, code in CITIES.items():
        if city in lo:
            found.setdefault(code, dict((c, n) for n, c in COUNTRY_NAMES).get(code, code))
    if _US_STATE.search(text):
        found.setdefault("US", "United States")
    return list(found.items())


def region_codes(region: str) -> Optional[set[str]]:
    """Country codes a remote region stands for; None when it means anywhere / unknown."""
    r = region.strip().lower()
    if any(w in r for w in _ANYWHERE):
        return None
    if r in ("us", "usa", "united states", "north america"):
        return {"US"} if r != "north america" else {"US", "CA", "MX"}
    if r in ("europe", "eu", "european union", "eea"):
        return set(EUROPE)
    if r in ("emea",):
        return set(EMEA)
    codes = {code for code, _ in countries_in(region)}
    return codes or set()


def open_to(description: Optional[str]) -> list[str]:
    """The 'Open to candidates in: …' list feeds put at the top of a description."""
    m = _OPEN_TO.search((description or "")[:4000])
    return [x.strip() for x in m.group(1).split(",") if x.strip()] if m else []


def location_match(location: Optional[str], regions: Iterable[str], preferred: Iterable[str],
                   remote: bool = False) -> Optional[bool]:
    """True: in (or open to) a target country · False: clearly outside · None: can't tell / no targets."""
    preferred = set(preferred or [])
    if not preferred:
        return None
    regions = [r for r in regions if r and r.strip()]
    if remote and regions:
        verdicts = []
        for r in regions:
            codes = region_codes(r)
            if codes is None:
                if any(w in r.lower() for w in _ANYWHERE):
                    return True
                continue
            if codes:
                verdicts.append(bool(codes & preferred))
        if any(verdicts):
            return True
        if verdicts:
            return False
    named = {code for code, _ in countries_in(location)}
    if named:
        if named & preferred:
            return True
        return None if remote and not regions else False
    if remote and location and any(w in location.lower() for w in _ANYWHERE):
        return True
    return None
