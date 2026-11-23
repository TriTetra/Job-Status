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
# Other ways postings name a country (whole words, any case)
COUNTRY_ALIASES = [
    ("United States of America", "US"), ("U.S.A.", "US"), ("U.S.", "US"),
    ("Great Britain", "GB"), ("England", "GB"), ("Scotland", "GB"), ("Wales", "GB"), ("Northern Ireland", "GB"),
    ("Britain", "GB"), ("Deutschland", "DE"), ("The Netherlands", "NL"), ("Nederland", "NL"), ("Holland", "NL"),
    ("España", "ES"), ("Espana", "ES"), ("Schweiz", "CH"), ("Suisse", "CH"), ("Svizzera", "CH"),
    ("Österreich", "AT"), ("Polska", "PL"), ("Italia", "IT"), ("Sverige", "SE"), ("Norge", "NO"),
    ("Danmark", "DK"), ("Suomi", "FI"), ("Belgique", "BE"), ("België", "BE"), ("Česko", "CZ"),
    ("Turkiye", "TR"), ("Republic of Korea", "KR"), ("Korea", "KR"), ("UAE", "AE"), ("KSA", "SA"),
    ("Pakistan", "PK"), ("Bangladesh", "BD"), ("Sri Lanka", "LK"), ("Peru", "PE"), ("Uruguay", "UY"),
    ("Costa Rica", "CR"), ("Morocco", "MA"), ("Tunisia", "TN"), ("Ghana", "GH"), ("Armenia", "AM"),
    ("Kuwait", "KW"), ("Bahrain", "BH"), ("Oman", "OM"), ("Jordan", "JO"), ("Lebanon", "LB"), ("Iceland", "IS"),
    ("Moldova", "MD"), ("Albania", "AL"), ("North Macedonia", "MK"), ("Bosnia", "BA"), ("Montenegro", "ME"),
    ("Kyrgyzstan", "KG"), ("Tajikistan", "TJ"), ("Mongolia", "MN"), ("Ethiopia", "ET"), ("Rwanda", "RW"),
    ("Uganda", "UG"), ("Tanzania", "TZ"), ("Senegal", "SN"), ("Ecuador", "EC"), ("Venezuela", "VE"),
    ("Guatemala", "GT"), ("Dominican Republic", "DO"), ("Puerto Rico", "US"), ("Taiwan", "TW"),
]
# Short codes postings use ("Remote - US", "Bangalore, IND", "London, UK"): upper case only,
# so "us" in "join us" never counts
CODE_ALIASES = {
    "US": "US", "USA": "US", "UK": "GB", "GB": "GB", "GBR": "GB", "DE": "DE", "DEU": "DE", "IND": "IN",
    "CAN": "CA", "FRA": "FR", "NLD": "NL", "ESP": "ES", "CHE": "CH", "POL": "PL", "PRT": "PT", "ITA": "IT",
    "IRL": "IE", "SWE": "SE", "NOR": "NO", "DNK": "DK", "FIN": "FI", "AUT": "AT", "BEL": "BE", "CZE": "CZ",
    "TUR": "TR", "ARE": "AE", "ISR": "IL", "SGP": "SG", "JPN": "JP", "AUS": "AU", "BRA": "BR", "MEX": "MX",
    "ARG": "AR", "COL": "CO", "CHN": "CN", "KOR": "KR", "UZB": "UZ", "KAZ": "KZ", "ROU": "RO", "HUN": "HU",
    "UAE": "AE", "NZ": "NZ", "NZL": "NZ",
}
US_STATES = [
    "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut", "Delaware", "Florida",
    "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland",
    "Massachusetts", "Michigan", "Minnesota", "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada",
    "New Hampshire", "New Jersey", "New Mexico", "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon",
    "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota", "Tennessee", "Texas", "Utah", "Vermont",
    "Virginia", "Washington State", "West Virginia", "Wisconsin", "Wyoming", "District of Columbia", "Washington, DC",
    "Washington DC", "Silicon Valley", "Bay Area",
]
CA_PROVINCES = ["Ontario", "Quebec", "Québec", "British Columbia", "Alberta", "Manitoba", "Saskatchewan",
                "Nova Scotia", "New Brunswick"]
# Cities that usually appear without their country
CITIES = {
    # GB
    "london": "GB", "manchester": "GB", "edinburgh": "GB", "cambridge, uk": "GB", "oxford": "GB", "bristol": "GB",
    "glasgow": "GB", "belfast": "GB", "leeds": "GB", "birmingham, uk": "GB", "newcastle upon tyne": "GB",
    # DE
    "berlin": "DE", "munich": "DE", "münchen": "DE", "hamburg": "DE", "frankfurt": "DE", "cologne": "DE",
    "köln": "DE", "stuttgart": "DE", "düsseldorf": "DE", "dusseldorf": "DE", "dresden": "DE", "leipzig": "DE",
    "karlsruhe": "DE", "heidelberg": "DE", "nuremberg": "DE", "nürnberg": "DE", "hannover": "DE", "hanover": "DE",
    "darmstadt": "DE", "aachen": "DE", "bonn": "DE", "tübingen": "DE", "freiburg": "DE",
    # CH, AT
    "zurich": "CH", "zürich": "CH", "geneva": "CH", "genève": "CH", "basel": "CH", "lausanne": "CH", "bern": "CH",
    "zug": "CH", "lugano": "CH", "vienna": "AT", "wien": "AT", "graz": "AT", "linz": "AT", "salzburg": "AT",
    # NL, BE, LU
    "amsterdam": "NL", "rotterdam": "NL", "utrecht": "NL", "eindhoven": "NL", "the hague": "NL", "den haag": "NL",
    "delft": "NL", "leiden": "NL", "groningen": "NL", "nieuwegein": "NL", "amstelveen": "NL", "haarlem": "NL",
    "brussels": "BE", "bruxelles": "BE", "antwerp": "BE", "ghent": "BE", "leuven": "BE",
    # FR, ES, PT, IT
    "paris": "FR", "lyon": "FR", "toulouse": "FR", "grenoble": "FR", "sophia antipolis": "FR", "bordeaux": "FR",
    "nantes": "FR", "lille": "FR", "marseille": "FR", "montpellier": "FR", "rennes": "FR",
    "madrid": "ES", "barcelona": "ES", "valencia": "ES", "seville": "ES", "sevilla": "ES", "málaga": "ES",
    "malaga": "ES", "bilbao": "ES", "lisbon": "PT", "lisboa": "PT", "porto": "PT", "braga": "PT",
    "milan": "IT", "milano": "IT", "rome": "IT", "roma": "IT", "turin": "IT", "torino": "IT", "bologna": "IT",
    # Nordics, Baltics
    "stockholm": "SE", "gothenburg": "SE", "göteborg": "SE", "malmö": "SE", "malmo": "SE",
    "copenhagen": "DK", "københavn": "DK", "aarhus": "DK", "oslo": "NO", "bergen": "NO", "trondheim": "NO",
    "helsinki": "FI", "espoo": "FI", "tampere": "FI", "oulu": "FI", "tallinn": "EE", "tartu": "EE",
    "vilnius": "LT", "riga": "LV",
    # Central and Eastern Europe
    "warsaw": "PL", "warszawa": "PL", "krakow": "PL", "kraków": "PL", "gdansk": "PL", "gdańsk": "PL",
    "wroclaw": "PL", "wrocław": "PL", "poznan": "PL", "poznań": "PL", "lodz": "PL", "łódź": "PL", "katowice": "PL",
    "prague": "CZ", "praha": "CZ", "brno": "CZ", "bratislava": "SK", "budapest": "HU", "bucharest": "RO",
    "cluj-napoca": "RO", "cluj": "RO", "sofia": "BG", "belgrade": "RS", "zagreb": "HR", "ljubljana": "SI",
    "athens": "GR", "kyiv": "UA", "kiev": "UA", "lviv": "UA", "dublin": "IE", "cork": "IE", "galway": "IE",
    "limassol": "CY", "nicosia": "CY", "valletta": "MT",
    # Turkey, Middle East, Central Asia
    "istanbul": "TR", "i̇stanbul": "TR", "ankara": "TR", "izmir": "TR", "i̇zmir": "TR", "bursa": "TR",
    "antalya": "TR", "kocaeli": "TR", "gebze": "TR", "dubai": "AE", "abu dhabi": "AE", "riyadh": "SA",
    "doha": "QA", "tel aviv": "IL", "haifa": "IL", "jerusalem": "IL", "tashkent": "UZ", "almaty": "KZ",
    "astana": "KZ", "baku": "AZ", "tbilisi": "GE", "cairo": "EG",
    # Americas
    "new york": "US", "san francisco": "US", "seattle": "US", "austin": "US", "boston": "US", "chicago": "US",
    "los angeles": "US", "san jose": "US", "palo alto": "US", "mountain view": "US", "sunnyvale": "US",
    "santa clara": "US", "menlo park": "US", "redmond": "US", "denver": "US", "atlanta": "US", "san diego": "US",
    "pittsburgh": "US", "miami": "US", "philadelphia": "US", "boulder": "US", "cupertino": "US",
    "toronto": "CA", "vancouver": "CA", "montreal": "CA", "montréal": "CA", "ottawa": "CA", "waterloo": "CA",
    "calgary": "CA", "são paulo": "BR", "sao paulo": "BR", "mexico city": "MX", "buenos aires": "AR",
    "bogotá": "CO", "bogota": "CO", "medellín": "CO", "medellin": "CO", "santiago": "CL", "lima": "PE",
    # Asia-Pacific
    "bangalore": "IN", "bengaluru": "IN", "hyderabad": "IN", "pune": "IN", "mumbai": "IN", "chennai": "IN",
    "gurgaon": "IN", "gurugram": "IN", "noida": "IN", "delhi": "IN", "tokyo": "JP", "osaka": "JP", "seoul": "KR",
    "beijing": "CN", "shanghai": "CN", "shenzhen": "CN", "taipei": "TW", "sydney": "AU", "melbourne": "AU",
    "brisbane": "AU", "auckland": "NZ", "manila": "PH", "jakarta": "ID", "bangkok": "TH", "kuala lumpur": "MY",
    "ho chi minh city": "VN", "hanoi": "VN",
}
EUROPE = {"DE", "GB", "FR", "NL", "CH", "SE", "NO", "DK", "FI", "ES", "PT", "IT", "PL", "AT", "BE", "IE", "CZ",
          "EE", "LV", "LT", "RO", "BG", "HU", "GR", "HR", "SI", "SK", "RS", "UA", "CY", "MT", "LU"}
EMEA = EUROPE | {"TR", "AE", "SA", "IL", "QA", "EG", "ZA", "NG", "KE", "GE", "AZ"}
_US_STATE = re.compile(r",\s*(CA|NY|TX|WA|MA|IL|CO|GA|NC|VA|AZ|FL|OH|PA|OR|UT|NV)\b")
_OPEN_TO = re.compile(r"Open to candidates in:\s*([^.\n]+)", re.I)
_ANYWHERE = ("worldwide", "global", "anywhere", "any country", "fully remote, any")


def _words(names) -> re.Pattern:
    """Any of the names as whole words, any case (a name never matches inside another word)."""
    alts = "|".join(re.escape(n) for n in sorted(names, key=len, reverse=True))
    return re.compile(rf"(?<![\w]){'(?:' + alts + ')'}(?![\w])", re.I)


_NAMED = [(n, c) for n, c in COUNTRY_NAMES] + COUNTRY_ALIASES
_NAME_RX = _words([n for n, _ in _NAMED])
_NAME_CODE = {n.lower(): c for n, c in _NAMED}
_CITY_RX = _words(CITIES)
_STATE_RX = _words(US_STATES)
_PROVINCE_RX = _words(CA_PROVINCES)
_CODE_RX = re.compile(rf"(?<![\w])({'|'.join(sorted(CODE_ALIASES, key=len, reverse=True))})(?![\w])")
_COUNTRY_NAME = {c: n for n, c in reversed(COUNTRY_NAMES)}
for _n, _c in COUNTRY_ALIASES:
    _COUNTRY_NAME.setdefault(_c, _n)


def countries_in(text: Optional[str]) -> list[tuple[str, str]]:
    """Every (code, name) named in a location string, in order of appearance, without repeats.
    Country names and their local / short forms, US states, Canadian provinces and cities."""
    if not text or text == "Unknown":
        return []
    hits: list[tuple[int, str]] = []
    hits += [(m.start(), _NAME_CODE.get(m.group(0).lower(), "")) for m in _NAME_RX.finditer(text)]
    hits += [(m.start(), CITIES[m.group(0).lower()]) for m in _CITY_RX.finditer(text) if m.group(0).lower() in CITIES]
    hits += [(m.start(), "US") for m in _STATE_RX.finditer(text)]
    hits += [(m.start(), "CA") for m in _PROVINCE_RX.finditer(text)]
    hits += [(m.start(), CODE_ALIASES[m.group(1)]) for m in _CODE_RX.finditer(text)]
    hits += [(m.start(), "US") for m in _US_STATE.finditer(text)]
    found: dict[str, str] = {}
    for _, code in sorted(hits):
        if code:
            found.setdefault(code, _COUNTRY_NAME.get(code, code))
    if "US" in found and "GE" in found and not re.search(r"tbilisi|batumi|kutaisi", text, re.I):
        found.pop("GE")  # "Atlanta, Georgia" is the US state
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
