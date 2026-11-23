"""How much to trust a posting and the company behind it, from what the posting itself shows.

No outside ratings are used (Glassdoor / Kununu don't allow automated access); these
are the signals a careful person checks by eye:

  + posted on the employer's own hiring system (an ATS board CareerOS reads)
  + the company has a website, the pay is stated, the posting is recent
  - posted by a recruiting agency for an unnamed client
  - open for many months (often not really hiring)
  - contact via a personal e-mail address
  ✗ warning signs of a scam: apply through WhatsApp / Telegram, a fee to pay,
    "earn $X a day", crypto / forex "trader" pitches

Levels: verified (employer's own board, nothing odd) · ok · caution · risk.
"""

import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Optional

STALE_DAYS = 120

_AGENCY_NAME = re.compile(
    r"recruit|staffing|headhunt|personalvermittlung|personaldienst|personalberatung|zeitarbeit|arbeitnehmerüberlassung|"
    r"executive search|search partners|talent (?:partners|solutions|acquisition)|hr solutions|"
    r"outsourcing|insan kaynaklar[ıi] (?:danışmanl|hizmet)|istihdam", re.I)
_AGENCY_TEXT = re.compile(
    r"on behalf of (?:our|a|an) (?:client|customer)|our client,? (?:a|an|is|based)|we are recruiting for|"
    r"für (?:unseren|einen) (?:kunden|mandanten)|im auftrag (?:unseres|eines) (?:kunden|mandanten)|unser (?:kunde|mandant) ist|"
    r"müşterimiz (?:için|olan)|çözüm ortağımız", re.I)
_SCAM = [
    (re.compile(r"(?:whats\s?app|telegram|signal)\W{0,3}.{0,40}(?:apply|contact|message|send (?:your|us)|reach)", re.I),
     "Asks you to apply through a chat app"),
    (re.compile(r"(?:pay|deposit|purchase)\W.{0,30}(?:training|equipment|registration|application|starter kit)\s*(?:fee|cost)?", re.I),
     "Asks for a payment"),
    (re.compile(r"earn\s+(?:up to\s+)?[$€£]\s?\d[\d,.]*\s*(?:k\s*)?(?:per|a|/)\s*(?:day|hour|week)", re.I),
     "Promises pay per day or hour up front"),
    (re.compile(r"(?:crypto|forex|binary option)s?\W.{0,40}(?:trader|trading|invest)", re.I),
     "Crypto / forex trading pitch"),
]
_PERSONAL_EMAIL = re.compile(r"[\w.+-]+@(?:gmail|yahoo|hotmail|outlook|proton(?:mail)?|icloud|yandex)\.(?:com|me|ru)", re.I)


@dataclass
class Trust:
    level: str                                  # verified | ok | caution | risk
    good: list[str] = field(default_factory=list)
    concerns: list[str] = field(default_factory=list)
    agency: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


def assess(*, company: str, description: str, ats: Optional[str], company_domain: Optional[str],
           salary_stated: bool, posted_at: Optional[datetime], now: Optional[datetime] = None,
           public: Optional[dict] = None) -> Trust:
    """`public`: what the public record says about the company (careeros/companies/facts.py::cached)."""
    now = now or datetime.now(timezone.utc)
    text = description or ""
    good, concerns, risks = [], [], []

    if ats:
        good.append("Posted on the employer's own hiring system")
    if company_domain:
        good.append(f"Company website: {company_domain}")
    if salary_stated:
        good.append("Pay is stated")

    agency = bool(_AGENCY_NAME.search(company or "") or _AGENCY_TEXT.search(text))
    if agency:
        concerns.append("Posted by a recruiting agency, not the employer itself")
    if _PERSONAL_EMAIL.search(text):
        concerns.append("Contact is a personal e-mail address")

    if posted_at:
        posted = posted_at if posted_at.tzinfo else posted_at.replace(tzinfo=timezone.utc)
        days = (now - posted).days
        if days > STALE_DAYS:
            concerns.append(f"Open for {days // 30} months: may not be actively hiring")
        elif days <= 30:
            good.append("Posted in the last month")

    if public:
        good += public.get("good") or []
        concerns += public.get("concerns") or []

    for rx, why in _SCAM:
        if rx.search(text):
            risks.append(why)

    if risks:
        return Trust("risk", good, risks + concerns, agency)
    if concerns:
        return Trust("caution", good, concerns, agency)
    if ats:
        return Trust("verified", good, [], agency)
    return Trust("ok", good, [], agency)
