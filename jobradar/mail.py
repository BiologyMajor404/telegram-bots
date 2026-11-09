"""Job alert emails: each subscriber gets a personal address in one shared mailbox.

Upwork, LinkedIn, Work.ua and others email job alerts to their users. A subscriber sends
those letters on to box+<token>@domain (Gmail delivers every +suffix to the same box), the
radar reads the box over IMAP and the token says whose letter it is. No passwords of the
job sites are involved, and no site is read against its rules.

The owner can also subscribe the box's own address to job alerts: letters without a token
are a source for everyone, read only from the sites the owner listed."""

import email
import email.policy
import imaplib
import logging
import re
import secrets
import ssl
from dataclasses import dataclass
from datetime import UTC, datetime
from email.message import EmailMessage
from email.utils import parseaddr, parsedate_to_datetime
from html.parser import HTMLParser

from jobradar.sources import plain

log = logging.getLogger(__name__)

TOKEN = re.compile(r"\+([0-9a-f]{10})@", re.IGNORECASE)
# Where a forwarded letter keeps the address it was really delivered to
ADDRESS_HEADERS = ("Delivered-To", "X-Original-To", "X-Forwarded-To", "Envelope-To", "To", "Cc")
LETTERS_PER_RUN = 30
IMAP_TIMEOUT = 30  # seconds; a stalled connection would stop the radar
TEXT_LIMIT = 15_000  # characters of a letter passed on to the AI
LINKS_LIMIT = 150  # a broad alert lists up to ~25 offers, each with a few links
GMAIL_LINK = re.compile(r"https://(?:mail-settings|mail)\.google\.com/\S+")
SHARED_FEED = "mail:shared"  # jobs from letters to the box's own address, for everyone
# Gmail's name in the Authentication-Results header it adds on top of every letter
GMAIL_CHECKS = "mx.google.com"
DMARC_PASS = re.compile(r"\bdmarc=pass\b[^;]*?\bheader\.from=([\w.-]+)", re.IGNORECASE)
DKIM_PASS = re.compile(r"\bdkim=pass\b[^;]*?\bheader\.(?:i=[^@\s;]*@|d=)([\w.-]+)", re.IGNORECASE)
# The subject of a "confirm your subscription" letter, in the languages of the job sites
CONFIRM = re.compile(
    r"confirm|verif|activat|potwierd|weryfik|aktywuj|aktywac|підтверд|активу|подтверд|"
    r"активир|bestätig",
    re.IGNORECASE,
)
CONFIRM_LINKS = 3


def within(domain: str, parent: str) -> bool:
    return domain == parent or domain.endswith("." + parent)


@dataclass(frozen=True)
class MailConfig:
    host: str
    address: str  # the shared box, e.g. jobradar.inbox@gmail.com
    password: str  # an app password, not the account's own
    # Sites whose letters to the box's own address are read for everyone, e.g. "pracuj.pl"
    senders: tuple[str, ...] = ()

    @property
    def enabled(self) -> bool:
        return bool(self.address and self.password)

    def personal(self, token: str) -> str:
        local, _, domain = self.address.partition("@")
        return f"{local}+{token}@{domain}"

    def site(self, sender: str) -> str | None:
        """The listed site a sender's domain belongs to, e.g. mail.pracuj.pl -> pracuj.pl."""
        return next((s for s in self.senders if within(sender, s)), None)


def new_token() -> str:
    return secrets.token_hex(5)  # 10 characters: unguessable enough for a mail address


@dataclass(frozen=True)
class Letter:
    token: str | None  # None: to the box's own address, a letter for everyone
    sender: str  # domain of the sender, shown as the source
    subject: str
    received: datetime
    text: str
    links: list[tuple[str, str]]  # (url, anchor text)
    verified: bool = False  # Gmail checked that it really comes from the sender's domain


class _Links(HTMLParser):
    """Links of an HTML letter with the text they are on."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            self._href = dict(attrs).get("href")
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._href:
            anchor = " ".join("".join(self._text).split())
            if self._href.startswith(("http://", "https://")):
                self.links.append((self._href, anchor[:200]))
            self._href = None


def _content(part: EmailMessage) -> str:
    try:
        return part.get_content()
    except (LookupError, UnicodeError):  # a charset Python doesn't know, or a wrong one
        return (part.get_payload(decode=True) or b"").decode("utf-8", errors="replace")


def _token(message: EmailMessage) -> str | None:
    for header in ADDRESS_HEADERS:
        for value in message.get_all(header, []):
            found = TOKEN.search(str(value))
            if found:
                return found[1].lower()
    return None


def _verified(message: EmailMessage, sender: str) -> bool:
    """Whether Gmail checked that the letter comes from the sender's domain: anyone can
    write "From: alerts@pracuj.pl", only pracuj.pl can sign for it. Gmail puts its own
    Authentication-Results on top; the ones below could be written by the sender."""
    results = message.get_all("Authentication-Results") or []
    if not sender or not results:
        return False
    top = " ".join(str(results[0]).split())
    if not top.lower().startswith(GMAIL_CHECKS):
        return False
    signed = [d.lower() for d in DMARC_PASS.findall(top) + DKIM_PASS.findall(top)]
    return any(within(sender, d) for d in signed)


def read_letter(raw: bytes) -> Letter:
    """A raw letter -> Letter; its token says whose letter it is."""
    message = email.message_from_bytes(raw, policy=email.policy.default)
    html_part = message.get_body(preferencelist=("html",))
    text_part = message.get_body(preferencelist=("plain",))
    links: list[tuple[str, str]] = []
    if html_part is not None:
        markup = _content(html_part)
        parser = _Links()
        parser.feed(markup)
        links, text = parser.links, plain(markup, TEXT_LIMIT)
    else:
        text = _content(text_part) if text_part is not None else ""
        links = [(url, "") for url in re.findall(r"https?://\S+", text)]
    try:
        received = parsedate_to_datetime(message.get("Date", ""))
    except (TypeError, ValueError):
        received = datetime.now(UTC)
    sender = parseaddr(message.get("From", ""))[1].rpartition("@")[2].lower()
    return Letter(
        token=_token(message),
        sender=sender,
        subject=str(message.get("Subject", ""))[:300],
        received=received if received.tzinfo else received.replace(tzinfo=UTC),
        text=text[:TEXT_LIMIT],
        links=list(dict.fromkeys(links))[:LINKS_LIMIT],
        verified=_verified(message, sender),
    )


def gmail_confirmation(letter: Letter) -> tuple[str, str] | None:
    """Gmail's "confirm forwarding" letter: its code and link, to pass on to the user."""
    if "forwarding confirmation" not in letter.subject.lower() or letter.sender != "google.com":
        return None
    code = re.search(r"#(\d+)", letter.subject)
    link = next((u for u, _ in letter.links if GMAIL_LINK.match(u)), None) or next(
        iter(GMAIL_LINK.findall(letter.text)), ""
    )
    return (code[1] if code else ""), link


def confirmation_links(letter: Letter) -> list[str] | None:
    """A site's "confirm your subscription" letter: the links that confirm it, to pass on
    to whoever subscribed. None for any other letter."""
    if not CONFIRM.search(letter.subject):
        return None
    links = [url for url, anchor in letter.links if CONFIRM.search(f"{anchor} {url}")]
    return links[:CONFIRM_LINKS] or None


def fetch_unseen(config: MailConfig, limit: int = LETTERS_PER_RUN) -> list[bytes]:
    """New letters of the box; fetching marks them read. Blocking: run it in a thread."""
    # imaplib doesn't check the server's certificate unless given a context that does
    context = ssl.create_default_context()
    with imaplib.IMAP4_SSL(config.host, ssl_context=context, timeout=IMAP_TIMEOUT) as box:
        box.login(config.address, config.password)
        box.select("INBOX")
        _, found = box.search(None, "UNSEEN")
        letters = []
        for number in found[0].split()[:limit]:
            _, data = box.fetch(number, "(RFC822)")
            letters += [part[1] for part in data if isinstance(part, tuple)]
        return letters
