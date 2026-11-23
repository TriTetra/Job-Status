"""Mailbox answers (careeros/applications/mail): only application mail is read, sure answers move
the application, unsure ones wait for the person, nothing is marked read."""

from datetime import datetime, timezone
from email.message import EmailMessage
from types import SimpleNamespace

import pytest

import careeros.db.models  # noqa: F401
from careeros.applications.mail import account, sync
from careeros.applications.mail.classify import Verdict, by_rules
from careeros.applications.mail.match import AppRef, company_words, match, own_domains
from careeros.applications.mail.reader import Header, body_text, parse_header

NOW = datetime(2026, 11, 23, 12, tzinfo=timezone.utc)


def _raw(sender: str, subject: str, body: str, html: bool = False, msg_id: str = "<1@x>") -> bytes:
    m = EmailMessage()
    m["From"], m["Subject"], m["Date"], m["Message-ID"] = sender, subject, "Mon, 23 Nov 2026 09:00:00 +0000", msg_id
    if html:
        m.set_content(f"<html><body><p>{body}</p></body></html>", subtype="html")
    else:
        m.set_content(body)
    return m.as_bytes()


def _h(sender_addr, name, subject, uid="1"):
    return Header(uid=uid, message_id=f"<{uid}@x>", from_addr=sender_addr, from_name=name, subject=subject, date=NOW)


ACME = AppRef(url="https://acme.ai/jobs/1", title="Machine Learning Engineer", company="Acme GmbH", status="applied",
              domains={"acme.ai"})
GLOBEX = AppRef(url="https://boards.greenhouse.io/globex/jobs/2", title="Backend Engineer", company="Globex",
                status="applied", domains=set())


def test_hosts_and_passwords():
    assert account.host_for("me@gmail.com") == "imap.gmail.com"
    assert account.host_for("me@company.io", "IMAP.Company.io") == "imap.company.io"
    for bad in [("me@unknown-provider.org", None), ("me@proton.me", None), ("not-an-email", None), ("me@x.io", "bad host!")]:
        with pytest.raises(account.MailError):
            account.host_for(*bad)
    assert account.clean_password("abcd efgh ijkl mnop") == "abcdefghijklmnop"
    assert account.clean_password(" my pass ") == "my pass"


def test_headers_and_bodies():
    h = parse_header("7", _raw("Acme Recruiting <jobs@acme.ai>", "Your application", "x"))
    assert (h.uid, h.from_addr, h.from_name, h.from_domain) == ("7", "jobs@acme.ai", "Acme Recruiting", "acme.ai")
    assert h.date.year == 2026 and h.key == parse_header("8", _raw("a@b.c", "other", "y")).key  # same Message-ID
    text = body_text(_raw("a@b.c", "s", "Thanks.\nUnfortunately we chose others.\n\nOn Mon, 1 Jan 2026 you wrote:\n> my cover letter"))
    assert "Unfortunately" in text and "cover letter" not in text
    assert body_text(_raw("a@b.c", "s", "Hello there", html=True)) == "Hello there"


def test_company_names_and_domains():
    assert company_words("Acme GmbH") == "acme" and company_words("Delivery Hero SE") == "delivery hero"
    assert company_words("AI") == "" and company_words("Remote") == ""
    assert own_domains("acme.ai", "https://careers.acme.co.uk/x", "https://boards.greenhouse.io/acme/1") == {"acme.ai", "acme.co.uk"}


def test_only_application_mail_matches():
    apps = [ACME, GLOBEX]
    assert match(_h("jobs@acme.ai", "Talent", "Update"), apps).app is ACME                          # company domain
    assert match(_h("no-reply@greenhouse.io", "Globex Hiring", "Your application"), apps).app is GLOBEX  # system + name
    assert match(_h("news@medium.com", "Medium", "Top stories for you"), apps) is None               # not read
    assert match(_h("alerts@linkedin.com", "LinkedIn", "New jobs like Backend Engineer"), apps) is None
    twins = [ACME, AppRef(url="https://acme.ai/jobs/9", title="Data Scientist", company="Acme", status="applied",
                          domains={"acme.ai"})]
    m = match(_h("jobs@acme.ai", "Acme", "Your application"), twins)
    assert m.ambiguous
    m = match(_h("jobs@acme.ai", "Acme", "Your application for Machine Learning Engineer"), twins)
    assert m.app is ACME and not m.ambiguous                                                          # title decides


def test_forward_moves_only():
    assert sync.target_for("rejection", "applied") == "rejected"
    assert sync.target_for("interview", "applied") == "interview"
    assert sync.target_for("interview", "offer") is None          # never backwards
    assert sync.target_for("rejection", "offer") is None
    assert sync.target_for("acknowledgment", "to_apply") == "applied"
    assert sync.target_for("acknowledgment", "applied") is None
    assert sync.target_for("info_request", "applied") is None


def test_rules_without_the_llm():
    assert by_rules("Your application", "Unfortunately we decided to move forward with other candidates.").kind == "rejection"
    assert by_rules("Next steps", "We'd like to schedule a call with you").kind == "interview"
    assert by_rules("Thanks", "We have received your application").kind == "acknowledgment"
    assert by_rules("Hi", "Our newsletter").kind == "other"


class _Session:
    def __init__(self):
        self.added = []

    def add(self, obj):
        self.added.append(obj)

    def flush(self):
        for i, o in enumerate(self.added, 1):
            o.id = o.id or i


def test_sure_answers_move_unsure_ones_wait(monkeypatch):
    moves = []
    monkeypatch.setattr(sync, "_move", lambda s, u, url, to, at, sid, actor=sync.ACTOR: moves.append((url, to, actor)) or "applied")
    app = AppRef(**{**ACME.__dict__})
    sig = sync.record(_Session(), "u1", _h("jobs@acme.ai", "Acme", "Update"), app,
                      Verdict("rejection", 0.95, "Unfortunately…", "llm"), ambiguous=False)
    assert (sig.state, sig.status_after, moves) == ("applied", "rejected", [(ACME.url, "rejected", "agent:mail")])

    moves.clear()
    for v, amb in [(Verdict("interview", 0.6, "", "llm"), False), (Verdict("interview", 0.99, "", "llm"), True),
                   (Verdict("interview", 0.6, "", "rules"), False)]:
        sig = sync.record(_Session(), "u1", _h("jobs@acme.ai", "Acme", "Next"), AppRef(**{**ACME.__dict__}), v, amb)
        assert sig.state == "pending" and sig.status_after == "interview"
    assert moves == []
    sig = sync.record(_Session(), "u1", _h("jobs@acme.ai", "Acme", "Thanks"), AppRef(**{**ACME.__dict__}),
                      Verdict("acknowledgment", 0.99, "", "llm"), False)
    assert sig.state == "noted" and moves == []                    # already applied: nothing to do
    sig = sync.record(_Session(), "u1", _h("jobs@acme.ai", "Acme", "Documents"), AppRef(**{**ACME.__dict__}),
                      Verdict("info_request", 0.9, "Please send your transcript", "llm"), False)
    assert sig.state == "pending" and sig.status_after is None     # they ask the person for something


class _Q:
    def __init__(self, rows=()):
        self.rows = list(rows)

    def filter(self, *a, **k):
        return self

    def all(self):
        return self.rows


class _CheckSession(_Session):
    def query(self, *a):
        return _Q()


class _Imap:
    """A read-only fake mailbox: records what was asked, never stores flags."""

    def __init__(self, messages):
        self.messages, self.calls = messages, []

    def select(self, box, readonly=False):
        self.calls.append(("select", box, readonly))
        return "OK", [b"3"]

    def uid(self, cmd, *args):
        self.calls.append((cmd, args[-1]))
        if cmd == "search":
            return "OK", [b" ".join(m[0].encode() for m in self.messages)]
        uids, what = args
        rows = []
        for uid, raw in self.messages:
            if uid in uids.split(","):
                part = raw.split(b"\n\n", 1)[0] if "HEADER" in what else raw
                rows.append((f"{uid} (UID {uid} BODY[] {{{len(part)}}}".encode(), part))
        return "OK", rows

    def logout(self):
        self.calls.append(("logout",))


def test_check_reads_only_application_mail_and_never_marks_it_read(monkeypatch):
    mailbox = _Imap([
        ("11", _raw("Acme Talent <talent@acme.ai>", "Your application", "Unfortunately we will not move forward.", msg_id="<a@x>")),
        ("12", _raw("Medium <noreply@medium.com>", "Daily digest", "Stories", msg_id="<b@x>")),
    ])
    acc = SimpleNamespace(last_synced_at=None, sync_status="connected")
    monkeypatch.setattr(account, "credentials", lambda s, u: ("imap.acme.ai", "me@x.io", "pw"))
    monkeypatch.setattr(account, "_account", lambda s, u: acc)
    monkeypatch.setattr(sync, "open_apps", lambda s, u, now: [AppRef(**{**ACME.__dict__})])
    monkeypatch.setattr(sync, "_move", lambda *a, **k: "applied")
    read = []

    def classifier(title, company, sender, subject, body):
        read.append(subject)
        return Verdict("rejection", 0.97, "we will not move forward", "llm")

    s = _CheckSession()
    out = sync.check(s, "u1", NOW, opener=lambda *c: mailbox, classifier=classifier)
    assert out["read"] == 2 and out["about_applications"] == 1 and out["applied"] == 1
    assert read == ["Your application"]                                     # the digest's body was never fetched
    assert ("select", "INBOX", True) in mailbox.calls and mailbox.calls[-1] == ("logout",)
    assert all("PEEK" in c[1] for c in mailbox.calls if c[0] == "fetch")    # nothing marked read
    assert acc.sync_status == "ok" and acc.last_synced_at == NOW
    assert [o.subject for o in s.added] == ["Your application"]              # only application mail is kept

    bad = SimpleNamespace(last_synced_at=None, sync_status="connected")
    monkeypatch.setattr(account, "_account", lambda s, u: bad)

    def refuse(*c):
        raise account.MailError("refused")
    assert sync.check(_CheckSession(), "u1", NOW, opener=refuse)["problem"] == "refused"
    assert bad.sync_status == "sign_in_failed"
