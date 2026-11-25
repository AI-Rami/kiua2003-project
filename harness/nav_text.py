"""Conservative, deterministic HTML preparation for NAV text captures."""

from html.parser import HTMLParser
import hashlib
import re


CLEANING_VERSION = "nav-contact-clean-v4"
EMAIL = re.compile(r"(?i)[\w.!#$%&'*+/=?^_`{|}~-]+@[\w.-]+\.[^\W\d_]{2,}\b")
# Common Norwegian landline/mobile formats, including numbers beside an icon label.
PHONE = re.compile(r"(?<!\d)(?!\d{4}-\d{2}-\d{2}\b|\d{2}\.\d{2}\.\d{4}\b)"
                   r"(?:\d[ .\u00a0-]?){7}\d(?!\d)")
INTERNATIONAL_PHONE = re.compile(r"(?<!\d)(?:\+|00)[ \u00a0]*(?:\d[ ().\u00a0-]*){7,14}\d(?!\d)")
REDACTION = "[redacted]"
JOB_CUE = re.compile(
    r"(?i)\b(?:du må|må kunne|er et krav|ønskelig|en fordel|erfaring med|"
    r"arbeidsoppgaver|du vil jobbe|you must|required|preferred|"
    r"experience with|you will work|you will develop)\b"
)
SENTENCE_BREAK = re.compile(
    r"(?<=[.!?;])\s+|(?<=[,;])\s+(?=(?:spør|ta kontakt|kontakt|for spørsmål|"
    r"ring|telefon|e-post|epost|ved spørsmål|ask|please contact|please reach out|"
    r"reach out to|get in touch|contact us|for questions|"
    r"phone|email)\b)", re.IGNORECASE
)


class Blocks(HTMLParser):
    BLOCK_TAGS = {"p", "div", "section", "article", "blockquote", "ul", "ol", "li",
                  "h1", "h2", "h3", "h4", "h5", "h6", "br", "table", "tr"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks = []
        self.parts = []
        self.kind = "p"
        self.hidden = 0

    def flush(self):
        value = re.sub(r"[ \t\r\f\v]+", " ", "".join(self.parts)).strip()
        if value:
            self.blocks.append((self.kind, value))
        self.parts = []
        self.kind = "p"

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.hidden += 1
            return
        if self.hidden:
            return
        if tag in self.BLOCK_TAGS:
            self.flush()
            self.kind = "li" if tag == "li" else "p"

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.hidden:
            self.hidden -= 1
            return
        if self.hidden:
            return
        if tag in self.BLOCK_TAGS:
            self.flush()

    def handle_data(self, data):
        if self.hidden:
            return
        self.parts.append(data)


def cleaned_input_issue(text):
    """Return a sanitized reason when edited text fails the automatic contact screen."""
    if not isinstance(text, str) or not text.strip() or not any(char.isalnum() for char in text):
        return "empty_cleaned_text"
    if EMAIL.search(text) or PHONE.search(text) or INTERNATIONAL_PHONE.search(text):
        return "remaining_email_or_phone"
    return None


def clean_description(html, contact_list=None):
    """Return (cleaned text or None, action counts, sanitized review reason)."""
    actions = {"redacted_emails": 0, "redacted_phones": 0}
    if not isinstance(html, str) or not html.strip():
        return None, actions, "missing_description"
    parser = Blocks()
    try:
        parser.feed(html)
        parser.flush()
    except (ValueError, OverflowError):
        return None, actions, "invalid_html"
    # The parser keeps visible text only. Never append structured contacts or link targets.
    lines = []
    for kind, value in parser.blocks:
        for passage in SENTENCE_BREAK.split(value):
            if JOB_CUE.search(passage) and cleaned_input_issue(passage) == "remaining_email_or_phone":
                # Keep ambiguous mixed requirements in the established human-review queue.
                return None, actions, "uncertain_mixed_contact_passage"
        value, emails = EMAIL.subn(REDACTION, value)
        value, international = INTERNATIONAL_PHONE.subn(REDACTION, value)
        value, domestic = PHONE.subn(REDACTION, value)
        actions["redacted_emails"] += emails
        actions["redacted_phones"] += international + domestic
        lines.append(("- " if kind == "li" else "") + value)
    text = "\n\n".join(lines)
    if not any(char.isalnum() for char in text.replace(REDACTION, "")):
        return None, actions, "no_safe_readable_text"
    if cleaned_input_issue(text):
        return None, actions, "uncertain_remaining_contact"
    return text, actions, None


def content_hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
