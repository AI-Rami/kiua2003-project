"""Conservative, deterministic HTML preparation for NAV text captures."""

from html.parser import HTMLParser
import hashlib
import re


CLEANING_VERSION = "nav-contact-clean-v3"
EMAIL = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
PHONE = re.compile(r"(?<!\d)(?:\+\s*47[ -]*)?(?:\d[ -]?){8}(?!\d)")
INTERNATIONAL_PHONE = re.compile(r"\+\d{1,3}[ -]?(?:\d[ -]?){7,12}")
CONTACT_START = re.compile(
    r"(?i)^(?:spør\b|ta (?:gjerne )?kontakt\b|kontaktinformasjon\b|kontaktperson\b|kontakt\s*[:\-]|"
    r"kontakt\s+[A-ZÆØÅ][a-zæøå-]+\s+[A-ZÆØÅ][a-zæøå-]+(?=\s+(?:på|om|for)\b|[.!?]|$)|"
    r"for spørsmål\b|ved spørsmål\b|spørsmål om (?:stillingen|rollen)\b|ring\s+(?:oss|meg|[A-ZÆØÅ])|"
    r"telefon\s*[:\-]|e-?post\s*[:\-]|send (?:din )?søknad til\b|"
    r"ask\b|please contact\b|please reach out\b|reach out to\b|"
    r"get in touch\b|contact us\b|contact person\b|"
    r"contact\s+[A-Z][a-z-]+\s+[A-Z][a-z-]+(?=\s+(?:about|at|for)\b|[.!?]|$)|"
    r"for questions\b|questions about (?:the role|this position)\b|"
    r"phone\s*[:\-]|email\s*[:\-])"
)
CONTACT_ANY = re.compile(
    r"(?i)\b(?:spør\s+.{1,90}\s+om\s+(?:rollen|stillingen)|"
    r"ta (?:gjerne )?kontakt|kontaktinformasjon|kontaktperson|kontakt\s+[A-ZÆØÅ][a-zæøå-]+\s+[A-ZÆØÅ][a-zæøå-]+(?=\s+(?:på|om|for)\b|[.!?]|$)|"
    r"for spørsmål|ved spørsmål|spørsmål om (?:stillingen|rollen)|"
    r"ring oss|telefon\s*[:\-]|e-?post\s*[:\-]|"
    r"ask\s+.{1,90}\s+about\s+(?:the role|this position)|"
    r"please contact|please reach out|reach out to|get in touch|contact us|contact person|"
    r"contact\s+[A-Z][a-z-]+\s+[A-Z][a-z-]+(?=\s+(?:about|at|for)\b|[.!?]|$)|for questions|"
    r"questions about (?:the role|this position)|phone\s*[:\-]|email\s*[:\-])\b"
)
JOB_CUE = re.compile(
    r"(?i)\b(?:du må|må kunne|er et krav|ønskelig|en fordel|erfaring med|"
    r"arbeidsoppgaver|du vil jobbe|you must|required|preferred|"
    r"experience with|you will work|you will develop)\b"
)
CONTACT_SECTION = re.compile(
    r"(?i)^(?:kontakt|kontaktperson|kontaktperson for stillingen|kontaktinformasjon|spørsmål|"
    r"contact|contact us|questions)$"
)
TEAM_SECTION = re.compile(r"(?i)^(?:våre ansatte|møt teamet|our team|meet the team)$")
JOB_HEADING = re.compile(
    r"(?i)^(?:kvalifikasjoner|arbeidsoppgaver|hva trenger vi deg til|"
    r"hvem er du|vi ser etter|vi tilbyr|om rollen|slik søker du|about the role|how to apply|"
    r"requirements|qualifications|responsibilities|what you will do|"
    r"what we offer|who you are)$"
)
SENTENCE_BREAK = re.compile(
    r"(?<=[.!?;])\s+|(?<=[,;])\s+(?=(?:spør|ta kontakt|kontakt|for spørsmål|"
    r"ring|telefon|e-post|epost|ved spørsmål|ask|please contact|please reach out|"
    r"reach out to|get in touch|contact us|for questions|"
    r"phone|email)\b)", re.IGNORECASE
)


def contact_hints(contact_list):
    """Extract explicit contact-list identifiers without persisting them."""
    hints = set()
    entries = contact_list if isinstance(contact_list, list) else [contact_list]
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        for key, value in entry.items():
            if key.casefold() in {"name", "email", "phone", "telephone", "mobile",
                                  "telefon", "epost", "e-post"}:
                if isinstance(value, str) and len(value.strip()) >= 4:
                    hints.add(value.strip().casefold())
        first = entry.get("firstName") or entry.get("firstname")
        last = entry.get("lastName") or entry.get("lastname")
        if isinstance(first, str) and isinstance(last, str) and first.strip() and last.strip():
            hints.add((first.strip() + " " + last.strip()).casefold())
    return hints


class Blocks(HTMLParser):
    BLOCK_TAGS = {"p", "div", "section", "article", "blockquote", "ul", "ol", "li",
                  "h1", "h2", "h3", "h4", "h5", "h6", "br", "table", "tr"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks = []
        self.parts = []
        self.bold_parts = []
        self.plain_parts = []
        self.bold_depth = 0
        self.kind = "p"
        self.link_labels = []
        self.anchor_stack = []
        self.hidden = 0

    def flush(self):
        value = re.sub(r"[ \t\r\f\v]+", " ", "".join(self.parts)).strip()
        if value:
            bold_only = bool("".join(self.bold_parts).strip()) and not "".join(self.plain_parts).strip()
            kind = "bold_heading" if self.kind == "p" and bold_only else self.kind
            self.blocks.append((kind, value, tuple(self.link_labels)))
        self.parts, self.bold_parts, self.plain_parts, self.link_labels = [], [], [], []
        self.kind = "p"

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.hidden += 1
            return
        if self.hidden:
            return
        if tag in self.BLOCK_TAGS:
            self.flush()
            self.kind = tag if re.fullmatch(r"h[1-6]", tag) else "li" if tag == "li" else "p"
        if tag in ("strong", "b"):
            self.bold_depth += 1
        if tag == "a":
            href = next((value for key, value in attrs if key == "href"), "") or ""
            flagged = href.lower().startswith(("mailto:", "tel:")) or bool(re.search(
                r"(?i)(?:/|#)(?:contact|kontakt)(?:[/?#]|$)", href))
            self.anchor_stack.append([flagged, []])

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.hidden:
            self.hidden -= 1
            return
        if self.hidden:
            return
        if tag in ("strong", "b") and self.bold_depth:
            self.bold_depth -= 1
        if tag == "a" and self.anchor_stack:
            flagged, pieces = self.anchor_stack.pop()
            if flagged:
                label = "".join(pieces).strip()
                if label:
                    self.link_labels.append(label)
        if tag in self.BLOCK_TAGS:
            self.flush()

    def handle_data(self, data):
        if self.hidden:
            return
        self.parts.append(data)
        (self.bold_parts if self.bold_depth else self.plain_parts).append(data)
        for flagged, pieces in self.anchor_stack:
            if flagged:
                pieces.append(data)


def _hint_found(passage, hints):
    folded = passage.casefold()
    return any(re.search(r"(?<!\w)" + re.escape(hint) + r"(?!\w)", folded) for hint in hints)


def _contact_signal(passage, hints, link_labels):
    return (bool(EMAIL.search(passage) or PHONE.search(passage)
                 or INTERNATIONAL_PHONE.search(passage) or CONTACT_ANY.search(passage))
            or (_hint_found(passage, hints) and bool(re.search(
                r"(?i)\b(?:kan svare på spørsmål|can answer questions)\b", passage)))
            or any(label and label.casefold() in passage.casefold() for label in link_labels))


def _standalone_contact(passage, hints, link_labels):
    value = passage.strip(" \t.,:;!?")
    return (value.casefold() in hints or value.casefold() in {label.casefold() for label in link_labels}
            or bool(EMAIL.fullmatch(value))
            or bool(PHONE.fullmatch(value)) or bool(INTERNATIONAL_PHONE.fullmatch(value)))


def cleaned_input_issue(text):
    """Return a sanitized reason when edited text fails the automatic contact screen."""
    if not isinstance(text, str) or not text.strip() or not any(char.isalnum() for char in text):
        return "empty_cleaned_text"
    if EMAIL.search(text) or PHONE.search(text) or INTERNATIONAL_PHONE.search(text):
        return "remaining_email_or_phone"
    if CONTACT_ANY.search(text):
        return "remaining_contact_wording"
    return None


def clean_description(html, contact_list=None):
    """Return (cleaned text or None, action counts, sanitized review reason)."""
    actions = {"removed_contact_passages": 0, "removed_contact_sections": 0,
               "removed_team_sections": 0, "contact_hint_passages": 0}
    if not isinstance(html, str) or not html.strip():
        return None, actions, "missing_description"
    parser = Blocks()
    try:
        parser.feed(html)
        parser.flush()
    except (ValueError, OverflowError):
        return None, actions, "invalid_html"
    hints = contact_hints(contact_list)
    retained = []
    section = None
    section_level = 7
    for kind, value, link_labels in parser.blocks:
        heading_level = int(kind[1]) if re.fullmatch(r"h[1-6]", kind) else None
        bold_heading = kind == "bold_heading"
        normalized_heading = value.strip(" :")
        if section:
            if (heading_level is not None and
                    (heading_level <= section_level or JOB_HEADING.fullmatch(normalized_heading))):
                section = None
            elif bold_heading and JOB_HEADING.fullmatch(normalized_heading):
                section = None
            elif bold_heading and not (CONTACT_SECTION.fullmatch(normalized_heading)
                                       or TEAM_SECTION.fullmatch(normalized_heading)):
                return None, actions, "uncertain_section_boundary"
        if section:
            continue
        if (heading_level is not None or bold_heading) and CONTACT_SECTION.fullmatch(normalized_heading):
            section, section_level = "contact", heading_level or 6
            actions["removed_contact_sections"] += 1
            continue
        if (heading_level is not None or bold_heading) and TEAM_SECTION.fullmatch(normalized_heading):
            section, section_level = "team", heading_level or 6
            actions["removed_team_sections"] += 1
            continue
        kept = []
        for passage in SENTENCE_BREAK.split(value):
            if not passage.strip():
                continue
            if not _contact_signal(passage, hints, link_labels):
                kept.append(passage)
                continue
            if _hint_found(passage, hints):
                actions["contact_hint_passages"] += 1
            hinted_contact_answer = (_hint_found(passage, hints) and bool(re.search(
                r"(?i)\b(?:kan svare på spørsmål|can answer questions)\b", passage)))
            if (not (CONTACT_START.search(passage.lstrip()) or _standalone_contact(passage, hints, link_labels)
                     or hinted_contact_answer)
                    or JOB_CUE.search(passage)):
                return None, actions, "uncertain_mixed_contact_passage"
            actions["removed_contact_passages"] += 1
        remaining = " ".join(kept).strip(" ,;\t")
        if remaining:
            retained.append((kind, remaining))
    lines = [("- " if kind == "li" else "") + value for kind, value in retained]
    text = "\n\n".join(lines).strip()
    if not text or not any(char.isalnum() for char in text):
        return None, actions, "no_safe_readable_text"
    if cleaned_input_issue(text):
        return None, actions, "uncertain_remaining_contact"
    return text, actions, None


def content_hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
