"""Posting text: HTML (escaped or not) and plain text → clean blocks, never markup."""

from careeros.jobs.posting import posting_blocks


def test_html_becomes_headings_paragraphs_and_items():
    raw = ("<p><strong>About the role</strong></p><p>Build the <a href='x'>ledger</a>.</p>"
           "<ul><li>Go and <em>Kafka</em></li><li>5+ years</li></ul><script>alert(1)</script>")
    assert posting_blocks(raw) == [
        {"type": "h", "text": "About the role"},
        {"type": "p", "text": "Build the ledger."},
        {"type": "li", "text": "Go and Kafka"},
        {"type": "li", "text": "5+ years"},
    ]


def test_escaped_html_from_greenhouse():
    raw = "&lt;h3&gt;What you'll do&lt;/h3&gt;&lt;p&gt;Ship &amp;amp; run services.&lt;/p&gt;"
    blocks = posting_blocks(raw)
    assert blocks[0] == {"type": "h", "text": "What you'll do"}
    assert blocks[1]["type"] == "p" and "Ship" in blocks[1]["text"]
    assert all("<" not in b["text"] for b in blocks)


def test_plain_text_lines():
    raw = "Responsibilities:\n• Own the API\n• Mentor engineers\n\nWe offer a great team."
    assert [b["type"] for b in posting_blocks(raw)] == ["h", "li", "li", "p"]


def test_empty():
    assert posting_blocks("") == [] and posting_blocks("   ") == []
