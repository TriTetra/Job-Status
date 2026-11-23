"""Comparing salaries across currencies: yearly amounts in US dollars.

Rates are approximate (late 2026) and only used to *rank* — a €70k and a $80k role
should land near each other, not to quote anyone a number. Unknown currencies
return None (treated as "not stated").
"""

from typing import Optional

USD_PER_UNIT = {
    "USD": 1.0, "EUR": 1.08, "GBP": 1.27, "CHF": 1.13, "CAD": 0.73, "AUD": 0.66, "NZD": 0.60,
    "SEK": 0.095, "NOK": 0.093, "DKK": 0.145, "PLN": 0.25, "CZK": 0.043, "HUF": 0.0027, "RON": 0.22,
    "TRY": 0.029, "AED": 0.27, "SAR": 0.27, "ILS": 0.27, "INR": 0.012, "SGD": 0.74, "JPY": 0.0066,
    "BRL": 0.18, "MXN": 0.055, "ZAR": 0.055, "UAH": 0.024,
}
PER_YEAR = {"year": 1, "yearly": 1, "annual": 1, "annually": 1, "month": 12, "monthly": 12}


def to_usd_year(amount, currency: Optional[str] = "USD", period: Optional[str] = "year") -> Optional[int]:
    """Yearly amount in USD, or None when it can't be converted."""
    try:
        value = float(amount)
    except (TypeError, ValueError):
        return None
    if value <= 0:
        return None
    rate = USD_PER_UNIT.get((currency or "USD").upper())
    times = PER_YEAR.get((period or "year").lower())
    if rate is None or times is None:
        return None
    return int(value * times * rate)
