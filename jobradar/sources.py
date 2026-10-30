"""Job boards the radar reads. Each source turns its feed into RawJob items.

Only public feeds and APIs are used; sites that block automated reading (Work.ua,
Freelancehunt, Upwork, LinkedIn) are left out on purpose. Subscribers can add their own
public Telegram channels, subreddits and RSS feeds."""

import asyncio
import codecs
import html
import ipaddress
import json
import logging
import re
import xml.etree.ElementTree as ET
from collections.abc import Awaitable, Callable, Iterable
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from urllib.parse import quote, urljoin, urlsplit
from zoneinfo import ZoneInfo

import aiohttp
from aiohttp.abc import ResolveResult
from aiohttp.resolver import ThreadedResolver
from yarl import URL

from jobradar.searches import REDDIT_SUBS

log = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (compatible; JobRadarBot/1.0)"
TIMEOUT = aiohttp.ClientTimeout(total=30)
KYIV = ZoneInfo("Europe/Kyiv")
TEXT_LIMIT = 6000  # characters of a description passed on to the AI
MARKUP_LIMIT = 500_000  # characters of HTML looked at when turning it into text
SLOW_CODECS = {"punycode", "idna"}
FEED_ITEMS = 50  # newest items read from one user feed
FETCH_ERRORS = (aiohttp.ClientError, TimeoutError, ValueError, KeyError, ET.ParseError)
# Plus network-level failures, e.g. a user's link resolving to no public address
READ_ERRORS = (*FETCH_ERRORS, OSError)


@dataclass(frozen=True)
class RawJob:
    source: str  # shown to the user, e.g. "robota.ua"
    external_id: str
    title: str
    text: str
    url: str
    published: datetime
    company: str = ""
    location: str = ""
    salary: str = ""
    # Which feed found it, e.g. "tg:channel"; a subscriber's own source has the same key
    feed: str = ""


Fetch = Callable[[aiohttp.ClientSession], Awaitable[list[RawJob]]]


@dataclass(frozen=True)
class Feed:
    name: str  # for logs
    fetch: Fetch


def plain(markup: str, limit: int = TEXT_LIMIT) -> str:
    """HTML -> readable plain text."""
    text = re.sub(r"<br\s*/?>|</p>|</li>|</h\d>", "\n", (markup or "")[:MARKUP_LIMIT], flags=re.I)
    # [^<>], not [^>]: on "<<<<…" without a ">" the latter takes quadratic time
    text = html.unescape(re.sub(r"<[^<>]*>", " ", text))
    lines = (re.sub(r"[ \t\xa0]+", " ", line).strip() for line in text.splitlines())
    return "\n".join(line for line in lines if line)[:limit]


def decode(body: bytes, charset: str | None) -> str:
    """A page's bytes as text in the charset its server named, UTF-8 if that one is unknown,
    isn't a text encoding, or is one that crawls on big input."""
    try:
        name = codecs.lookup(charset or "utf-8").name
    except LookupError:
        name = "utf-8"
    if name in SLOW_CODECS:
        name = "utf-8"
    try:
        return body.decode(name, errors="replace")
    except LookupError:  # e.g. "base64": a codec, but not for text
        return body.decode("utf-8", errors="replace")


def salary_range(low: object, high: object, currency: object = "", period: object = "") -> str:
    parts = [str(int(float(v))) for v in (low, high) if v and float(v) > 0]
    if not parts:
        return ""
    return " ".join(p for p in ("–".join(parts), str(currency or ""), str(period or "")) if p)


async def _get(http: aiohttp.ClientSession, url: str) -> str:
    async with http.get(url) as response:
        response.raise_for_status()
        return await response.text()


# --- robota.ua: the biggest Ukrainian board with an open API ---

ROBOTA_REMOTE = 3  # scheduleId of "remote work"


async def robota(http: aiohttp.ClientSession, queries: Iterable[str]) -> list[RawJob]:
    jobs: dict[str, RawJob] = {}
    for query in queries:
        url = (
            f"https://api.rabota.ua/vacancy/search?keyWords={quote(query)}"
            f"&scheduleId={ROBOTA_REMOTE}"
        )
        try:
            page = await _get(http, url)
        except aiohttp.ClientResponseError as e:
            # The API now and then answers 400 to one query; the others still count
            log.warning("robota.ua query %r failed: %s", query, e.status)
            continue
        for doc in json.loads(page).get("documents", []):
            job_id = str(doc["id"])
            jobs[job_id] = RawJob(
                source="robota.ua",
                external_id=job_id,
                title=doc.get("name", ""),
                text=plain(doc.get("shortDescription", "")),
                url=f"https://robota.ua/company{doc.get('notebookId')}/vacancy{job_id}",
                published=datetime.fromisoformat(doc["date"][:19]).replace(tzinfo=KYIV),
                company=doc.get("companyName", ""),
                location=f"{doc.get('cityName', '')}, remote",
                salary=salary_range(doc.get("salaryFrom"), doc.get("salaryTo"), "UAH")
                or (f"{doc['salary']} UAH" if doc.get("salary") else ""),
                feed="board:robota",
            )
    return list(jobs.values())


async def robota_details(http: aiohttp.ClientSession, job: RawJob) -> RawJob:
    """The search only has a short excerpt; the full text comes from the vacancy itself."""
    doc = json.loads(await _get(http, f"https://api.rabota.ua/vacancy?id={job.external_id}"))
    text = plain(doc.get("description", ""))
    comment = doc.get("salaryComment") or ""
    return replace(job, text=text or job.text, salary=" ".join(filter(None, [job.salary, comment])))


# --- International remote boards ---


async def himalayas(http: aiohttp.ClientSession, queries: Iterable[str]) -> list[RawJob]:
    jobs: dict[str, RawJob] = {}
    for query in queries:
        data = json.loads(
            await _get(http, f"https://himalayas.app/jobs/api/search?q={quote(query)}")
        )
        for j in data.get("jobs", []):
            jobs[j["guid"]] = RawJob(
                source="Himalayas",
                external_id=j["guid"][-128:],
                title=j.get("title", ""),
                text=plain(j.get("description", "")),
                url=j["applicationLink"],
                published=datetime.fromtimestamp(int(j["pubDate"]), UTC),
                company=j.get("companyName", ""),
                location=", ".join(j.get("locationRestrictions") or []) or "Worldwide",
                salary=salary_range(
                    j.get("minSalary"), j.get("maxSalary"), j.get("currency"), j.get("salaryPeriod")
                ),
                feed="board:himalayas",
            )
    return list(jobs.values())


async def remoteok(http: aiohttp.ClientSession) -> list[RawJob]:
    # The newest jobs of every kind: the API ignores search parameters. The first item is
    # its legal notice; Remote OK asks for a link back, which every card has
    data = json.loads(await _get(http, "https://remoteok.com/api"))[1:]
    return [
        RawJob(
            source="Remote OK",
            external_id=str(j["id"]),
            title=j.get("position", ""),
            text=plain(j.get("description", "")),
            url=j["url"],
            published=datetime.fromisoformat(j["date"]),
            company=j.get("company", ""),
            location=j.get("location") or "Worldwide",
            salary=salary_range(j.get("salary_min"), j.get("salary_max"), "USD", "year"),
            feed="board:remoteok",
        )
        for j in data
    ]


async def remotive(http: aiohttp.ClientSession) -> list[RawJob]:
    # Like Remote OK, it returns the newest jobs whatever the search says
    data = json.loads(await _get(http, "https://remotive.com/api/remote-jobs"))
    return [
        RawJob(
            source="Remotive",
            external_id=str(j["id"]),
            title=j.get("title", ""),
            text=plain(j.get("description", "")),
            url=j["url"],
            published=datetime.fromisoformat(j["publication_date"]).replace(tzinfo=UTC),
            company=j.get("company_name", ""),
            location=j.get("candidate_required_location", ""),
            salary=j.get("salary", ""),
            feed="board:remotive",
        )
        for j in data.get("jobs", [])
    ]


# --- Reddit: freelance "[Hiring]" posts, often the hottest ones ---

REDDIT_SEARCH = "https://www.reddit.com/r/{subs}/search.rss?q={query}&restrict_sr=1&sort=new"
REDDIT_NEW = "https://www.reddit.com/r/{subs}/new.rss?limit=100"
REDDIT_BATCH = 20  # subreddits per request; one request per batch keeps Reddit happy
ATOM = "{http://www.w3.org/2005/Atom}"


def parse_reddit(page: str) -> list[RawJob]:
    jobs = []
    for entry in ET.fromstring(page).iter(f"{ATOM}entry"):
        link = entry.find(f"{ATOM}link")
        category = entry.find(f"{ATOM}category")
        sub = category.get("term", "") if category is not None else ""
        jobs.append(
            RawJob(
                source=f"Reddit r/{sub}",
                external_id=entry.findtext(f"{ATOM}id", ""),
                title=html.unescape(entry.findtext(f"{ATOM}title", "")),
                text=plain(entry.findtext(f"{ATOM}content", "")),
                url=link.get("href", "") if link is not None else "",
                published=datetime.fromisoformat(entry.findtext(f"{ATOM}updated", "")),
                feed=f"reddit:{sub.lower()}",
            )
        )
    return jobs


async def reddit(http: aiohttp.ClientSession, terms: Iterable[str]) -> list[RawJob]:
    """One search across all hiring subreddits, so Reddit gets one request per run."""
    query = quote(" OR ".join(terms))
    subs = "+".join(REDDIT_SUBS)
    return parse_reddit(await _get(http, REDDIT_SEARCH.format(subs=subs, query=query)))


def subreddits(subs: list[str]) -> Fetch:
    """New posts of the given subreddits; the editing filter picks the jobs out of them."""

    async def fetch(http: aiohttp.ClientSession) -> list[RawJob]:
        jobs = []
        for i in range(0, len(subs), REDDIT_BATCH):
            batch = "+".join(subs[i : i + REDDIT_BATCH])
            jobs += parse_reddit(await _get(http, REDDIT_NEW.format(subs=batch)))
        return jobs

    return fetch


# --- Ukrainian boards with official feeds: DOU, Djinni; and the Freelancehunt API ---

DOU_FEED = "https://jobs.dou.ua/vacancies/feeds/?search={query}"
DJINNI_FEED = "https://djinni.co/jobs/rss/"  # the newest jobs; it ignores search words
WWR_FEED = "https://weworkremotely.com/remote-jobs.rss"  # likewise, every category
FREELANCEHUNT_API = "https://api.freelancehunt.com/v2/projects"
FREELANCEHUNT_PAGES = 3


def as_board(jobs: list[RawJob], source: str, key: str) -> list[RawJob]:
    return [replace(j, source=source, feed=key) for j in jobs]


async def dou(http: aiohttp.ClientSession, queries: Iterable[str]) -> list[RawJob]:
    jobs: dict[str, RawJob] = {}
    for query in queries:
        url = DOU_FEED.format(query=quote(query))
        for job in parse_feed(await _get(http, url), url):
            jobs[job.external_id] = job
    return as_board(list(jobs.values()), "DOU", "board:dou")


async def djinni(http: aiohttp.ClientSession) -> list[RawJob]:
    return as_board(
        parse_feed(await _get(http, DJINNI_FEED), DJINNI_FEED), "Djinni", "board:djinni"
    )


async def weworkremotely(http: aiohttp.ClientSession) -> list[RawJob]:
    jobs = parse_feed(await _get(http, WWR_FEED), WWR_FEED)
    return as_board(jobs, "We Work Remotely", "board:wwr")


def parse_freelancehunt(data: dict) -> list[RawJob]:
    jobs = []
    for project in data.get("data", []):
        a = project.get("attributes", {})
        budget = a.get("budget") or {}
        location = a.get("location") or {}
        skills = ", ".join(s.get("name", "") for s in a.get("skills") or [])
        jobs.append(
            RawJob(
                source="Freelancehunt",
                external_id=str(project["id"]),
                title=a.get("name", ""),
                text=plain(a.get("description_html") or a.get("description") or "")
                + (f"\nSkills: {skills}" if skills else ""),
                url=project.get("links", {}).get("self", {}).get("web", ""),
                published=datetime.fromisoformat(a["published_at"]),
                location="remote" if a.get("is_remote_job") else str(location.get("city", "")),
                salary=" ".join(
                    str(v) for v in (budget.get("amount"), budget.get("currency")) if v
                ),
                feed="board:freelancehunt",
            )
        )
    return jobs


async def freelancehunt(http: aiohttp.ClientSession, token: str) -> list[RawJob]:
    """The newest projects through the official API, with the user's personal token.
    A page holds 10, so read a few: more than that can appear between two runs."""
    headers = {"Authorization": f"Bearer {token}"}
    jobs: list[RawJob] = []
    for page in range(1, FREELANCEHUNT_PAGES + 1):
        url = f"{FREELANCEHUNT_API}?page[number]={page}"
        async with http.get(url, headers=headers) as response:
            response.raise_for_status()
            jobs += parse_freelancehunt(await response.json())
    return jobs


# --- Public Telegram channels, read through their web preview t.me/s/<channel> ---

TG_POST = re.compile(r'data-post="([\w/]+)"')
TG_TEXT = re.compile(r'class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>', re.S)
TG_TIME = re.compile(r'<time datetime="([^"]+)"')


def parse_channel(page: str) -> list[RawJob]:
    jobs = []
    # One block per post, so a post without text can't borrow the next post's text
    for block in page.split('class="tgme_widget_message_wrap')[1:]:
        post, text, time = TG_POST.search(block), TG_TEXT.search(block), TG_TIME.search(block)
        if not (post and text and time):
            continue
        body = plain(text[1])
        if not body:  # e.g. only an emoji image
            continue
        channel = post[1].split("/")[0]
        jobs.append(
            RawJob(
                source=f"Telegram @{channel}",
                external_id=post[1],
                title=body.splitlines()[0][:200],
                text=body,
                url=f"https://t.me/{post[1]}",
                published=datetime.fromisoformat(time[1]),
                feed=f"tg:{channel.lower()}",
            )
        )
    return jobs


def telegram(channel: str) -> Fetch:
    async def fetch(http: aiohttp.ClientSession) -> list[RawJob]:
        return parse_channel(await _get(http, f"https://t.me/s/{channel}"))

    return fetch


# --- RSS and Atom feeds added by subscribers ---

FEED_BYTES = 2_000_000
REDIRECTS = 3
INTERNAL_SUFFIXES = (".localhost", ".local", ".internal", ".lan", ".home.arpa")


class PublicOnlyResolver(ThreadedResolver):
    """Resolves only to public addresses, so a link from a user can't reach the
    database, Redis or anything else inside the server's network."""

    async def resolve(self, host: str, port: int = 0, family: int = 0) -> list[ResolveResult]:
        found = await super().resolve(host, port, family)
        public = [r for r in found if ipaddress.ip_address(r["host"]).is_global]
        if not public:
            raise OSError(f"{host} has no public address")
        return public


def check_public_url(url: str) -> None:
    """Plain http(s) on the standard ports, no addresses inside the network."""
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https") or not parts.hostname:
        raise ValueError(f"not a web link: {url}")
    if parts.port not in (None, 80, 443) or parts.username or parts.password:
        raise ValueError(f"unusual link: {url}")
    # The host as aiohttp will connect to it: yarl turns e.g. fullwidth "１２７.０.０.１"
    # into "127.0.0.1"
    try:
        host = (URL(url).host or "").rstrip(".").lower()
    except ValueError:
        raise ValueError(f"not a web link: {url}") from None
    try:
        literal = ipaddress.ip_address(host)
    except ValueError:
        # Numbers in a form no public link uses: "127.1", "0177.0.0.1", "0x7f.0.0.1"
        if re.fullmatch(r"[\d.]+|.*\.(0x[\da-f]*|\d+)", host):
            raise ValueError(f"unusual address: {url}") from None
        # Names like "redis" or "localhost" only mean something inside the server's network;
        # for public names the resolver checks where they point
        if "." not in host or host.endswith(INTERNAL_SUFFIXES):
            raise ValueError(f"internal host: {url}") from None
        return
    # aiohttp connects to IP literals without asking the resolver
    if not literal.is_global:
        raise ValueError(f"address inside the network: {url}")


async def fetch_public(url: str) -> str:
    """Download a page from a link a user gave: size-capped, redirects checked one by one."""
    connector = aiohttp.TCPConnector(resolver=PublicOnlyResolver())
    async with aiohttp.ClientSession(
        timeout=TIMEOUT, headers={"User-Agent": USER_AGENT}, connector=connector
    ) as http:
        for _ in range(REDIRECTS + 1):
            check_public_url(url)
            async with http.get(url, allow_redirects=False) as response:
                if response.status in (301, 302, 303, 307, 308):
                    url = urljoin(url, response.headers.get("Location", ""))
                    continue
                response.raise_for_status()
                body = bytearray()
                # read(n) returns whatever has arrived, so collect chunks up to the cap
                while chunk := await response.content.read(64_000):
                    body += chunk
                    if len(body) > FEED_BYTES:
                        raise ValueError(f"feed is too large: {url}")
                return decode(bytes(body), response.charset)
    raise ValueError(f"too many redirects: {url}")


def feed_date(value: str | None) -> datetime:
    """RSS dates are RFC 822, Atom ones ISO 8601; an undated item counts as new."""
    if value:
        for parse in (parsedate_to_datetime, datetime.fromisoformat):
            try:
                parsed = parse(value.strip())
            except (TypeError, ValueError, IndexError):
                continue
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
    return datetime.now(UTC)


def parse_feed(page: str, url: str) -> list[RawJob]:
    """RSS 2.0 or Atom -> jobs. Raises ET.ParseError if the page isn't a feed."""
    # Feeds don't need entities of their own, and nested ones blow up a small page into
    # a hundred times as much text
    if "<!ENTITY" in page:
        raise ET.ParseError("feeds with entity declarations aren't read")
    root = ET.fromstring(page)
    host = urlsplit(url).hostname or url
    items: list[tuple[str, str, str, str, str, str]] = []  # id, title, link, text, date, region
    for item in root.iter("item"):
        link = item.findtext("link", "").strip()
        items.append(
            (
                item.findtext("guid", "") or link,
                item.findtext("title", ""),
                link,
                item.findtext("description", ""),
                item.findtext("pubDate", ""),
                item.findtext("region", ""),
            )
        )
    for entry in root.iter(f"{ATOM}entry"):
        link_el = entry.find(f"{ATOM}link")
        link = link_el.get("href", "") if link_el is not None else ""
        items.append(
            (
                entry.findtext(f"{ATOM}id", "") or link,
                entry.findtext(f"{ATOM}title", ""),
                link,
                entry.findtext(f"{ATOM}content", "") or entry.findtext(f"{ATOM}summary", ""),
                entry.findtext(f"{ATOM}published", "") or entry.findtext(f"{ATOM}updated", ""),
                "",
            )
        )
    if not items and root.tag not in ("rss", f"{ATOM}feed"):
        raise ET.ParseError("not an RSS or Atom feed")
    return [
        RawJob(
            source=host,
            external_id=(item_id or link)[-128:],
            title=html.unescape(title).strip()[:200],
            text=plain(text),
            url=link,
            published=feed_date(date),
            location=region.strip()[:120],
            feed=f"rss:{url}",
        )
        for item_id, title, link, text, date, region in items[:FEED_ITEMS]
        if (item_id or link) and link.startswith(("http://", "https://"))
    ]


def rss(url: str) -> Fetch:
    async def fetch(_http: aiohttp.ClientSession) -> list[RawJob]:
        page = await fetch_public(url)
        # Anyone's page, up to 2 MB: parsed aside, so the bot keeps answering meanwhile
        return await asyncio.to_thread(parse_feed, page, url)

    return fetch


# --- All feeds together ---

BOARD_KEYS = {
    "board:robota",
    "board:himalayas",
    "board:remoteok",
    "board:remotive",
    "board:dou",
    "board:djinni",
    "board:wwr",
    "board:freelancehunt",
}
# Sources whose list has only an excerpt: by RawJob.feed
DETAILS = {"board:robota": robota_details}


def global_feeds(
    channels: list[str], queries: list[str], freelancehunt_token: str = ""
) -> list[Feed]:
    """The shared feeds, searching job boards for what subscribers look for."""

    async def robota_feed(http: aiohttp.ClientSession) -> list[RawJob]:
        return await robota(http, queries)

    async def himalayas_feed(http: aiohttp.ClientSession) -> list[RawJob]:
        return await himalayas(http, queries)

    async def reddit_feed(http: aiohttp.ClientSession) -> list[RawJob]:
        return await reddit(http, [f'"{q}"' for q in queries])

    async def dou_feed(http: aiohttp.ClientSession) -> list[RawJob]:
        return await dou(http, queries)

    async def freelancehunt_feed(http: aiohttp.ClientSession) -> list[RawJob]:
        return await freelancehunt(http, freelancehunt_token)

    feeds = [
        Feed("robota.ua", robota_feed),
        Feed("Himalayas", himalayas_feed),
        Feed("Remote OK", remoteok),
        Feed("Remotive", remotive),
        Feed("Reddit", reddit_feed),
        Feed("DOU", dou_feed),
        Feed("Djinni", djinni),
        Feed("We Work Remotely", weworkremotely),
        *(Feed(f"@{c}", telegram(c)) for c in channels),
    ]
    # Its API is meant for users with a personal token, so without one it stays off
    if freelancehunt_token:
        feeds.append(Feed("Freelancehunt", freelancehunt_feed))
    return feeds


def global_keys(channels: list[str]) -> set[str]:
    """Feeds every subscriber gets jobs from."""
    return BOARD_KEYS | {f"reddit:{s}" for s in REDDIT_SUBS} | {f"tg:{c}" for c in channels}


def user_feeds(sources: Iterable[tuple[str, str]], skip: set[str]) -> list[Feed]:
    """Feeds for the subscribers' own sources (kind, ref), each fetched once."""
    keys = {f"{kind}:{ref}" for kind, ref in sources} - skip
    feeds = []
    subs = sorted(k.removeprefix("reddit:") for k in keys if k.startswith("reddit:"))
    if subs:
        feeds.append(Feed("own subreddits", subreddits(subs)))
    for key in sorted(keys):
        kind, _, ref = key.partition(":")
        if kind == "tg":
            feeds.append(Feed(f"@{ref}", telegram(ref)))
        elif kind == "rss":
            feeds.append(Feed(ref, rss(ref)))
    return feeds


def session() -> aiohttp.ClientSession:
    return aiohttp.ClientSession(timeout=TIMEOUT, headers={"User-Agent": USER_AGENT})


async def fetch_all(http: aiohttp.ClientSession, feeds: list[Feed]) -> list[RawJob]:
    """One broken or blocked source must not stop the others."""
    results = await asyncio.gather(*(f.fetch(http) for f in feeds), return_exceptions=True)
    jobs: list[RawJob] = []
    for feed, result in zip(feeds, results, strict=True):
        if isinstance(result, READ_ERRORS):
            log.warning("Source %s failed: %r", feed.name, result)
        elif isinstance(result, Exception):
            # Something its parser didn't expect, e.g. a board changed its format
            log.error("Source %s failed", feed.name, exc_info=result)
        elif isinstance(result, BaseException):
            raise result  # cancelled: the bot is stopping
        else:
            jobs += result
    return jobs


async def with_details(http: aiohttp.ClientSession, job: RawJob) -> RawJob:
    details = DETAILS.get(job.feed)
    if details is None:
        return job
    try:
        return await details(http, job)
    except FETCH_ERRORS as e:
        log.warning("Details of %s failed: %r", job.url, e)
        return job
