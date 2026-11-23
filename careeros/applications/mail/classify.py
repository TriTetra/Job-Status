"""What an employer's e-mail says about an application: rejection, interview, offer, a request
for information, an automatic acknowledgment, or something else.

The LLM reads it (task "mail_classify") and quotes the sentence that shows it. Without the
LLM, plain phrase rules give a low-confidence guess that the person confirms.
"""

import logging
import re
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)

Kind = Literal["rejection", "interview", "offer", "info_request", "acknowledgment", "other"]


class MailVerdict(BaseModel):
    about_this_application: bool = True
    kind: Kind = "other"
    confidence: float = Field(default=0.5, ge=0, le=1)
    evidence: str = ""

    @field_validator("evidence")
    @classmethod
    def _short(cls, v: str) -> str:
        return " ".join((v or "").split())[:280]


@dataclass
class Verdict:
    kind: str
    confidence: float
    evidence: str
    by: str              # "llm" | "rules"


SYSTEM = ("You read e-mails a job seeker received and say what they mean for one application. "
          "Judge only from the e-mail. Return one JSON object.")

PROMPT = """The person applied to "{title}" at {company}.

E-mail from: {sender}
Subject: {subject}

{body}

Return JSON with exactly these keys:
- about_this_application: false if this e-mail is not about that application (a job alert, a newsletter, another company or role).
- kind: one of
  rejection (they won't move forward with the person),
  interview (an invitation to a call, interview, assessment, take-home task or next round, or a request to book a time),
  offer (a job offer),
  info_request (they ask for documents, answers or details, without inviting to a next round),
  acknowledgment (an automatic "we received your application"),
  other.
- confidence: 0 to 1, how sure you are of the kind.
- evidence: the one sentence from the e-mail that shows it, quoted exactly (max 200 characters)."""

_RULES = [
    ("rejection", re.compile(r"(unfortunately|regret to inform|decided (not )?to (move|proceed) forward with other|"
                             r"not (to )?(move|proceed) forward|will not be (moving|proceeding)|other candidates|"
                             r"position has been filled|not be progressing|maalesef|olumsuz)", re.I)),
    ("offer", re.compile(r"(pleased to offer|offer letter|job offer|we('d| would) like to offer you)", re.I)),
    ("interview", re.compile(r"(schedule (a|an|your) (call|interview|chat)|invite you to (an? )?(interview|call|chat)|"
                             r"next (step|round)|availability for|book a time|calendly\.com|take[- ]home|"
                             r"coding (challenge|assessment)|mülakat|görüşme)", re.I)),
    ("acknowledgment", re.compile(r"(received your application|thank(s| you) for (applying|your application|your interest)|"
                                  r"application (has been )?(received|submitted)|başvurunuz (alındı|ulaştı))", re.I)),
]


def by_rules(subject: str, body: str) -> Verdict:
    text = f"{subject}\n{body}"
    for kind, rx in _RULES:
        m = rx.search(text)
        if m:
            start = max(0, m.start() - 80)
            return Verdict(kind, 0.6, " ".join(text[start:m.end() + 80].split())[:280], "rules")
    return Verdict("other", 0.3, "", "rules")


def classify(title: str, company: str, sender: str, subject: str, body: str) -> Verdict:
    from careeros.shared.llm import get_llm_client

    try:
        v = get_llm_client().complete_model(
            PROMPT.format(title=title or "a role", company=company or "the company", sender=sender,
                          subject=subject, body=(body or "")[:5000]),
            MailVerdict, system=SYSTEM, task="mail_classify", temperature=0.0, max_tokens=250, timeout=60)
    except Exception as e:  # not configured, budget, bad output: the phrase rules, always confirmed by the person
        logger.info("Mail classification fell back to rules: %s", type(e).__name__)
        return by_rules(subject, body)
    if not v.about_this_application:
        return Verdict("other", v.confidence, v.evidence, "llm")
    return Verdict(v.kind, v.confidence, v.evidence, "llm")
