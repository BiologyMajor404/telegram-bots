"""JobRadar: job alert emails sent on to a subscriber's personal address."""

from datetime import UTC, datetime
from email.message import EmailMessage

from jobradar.ai import letter_jobs, letter_prompt
from jobradar.config import MAIL_SENDERS, JobRadarSettings
from jobradar.mail import (
    MailConfig,
    confirmation_links,
    gmail_confirmation,
    new_token,
    read_letter,
)

BOX = MailConfig("imap.gmail.com", "jobradar.inbox@gmail.com", "app-password")
# What Gmail writes on top of a genuine letter from pracuj.pl
GENUINE = (
    "mx.google.com; dkim=pass header.i=@pracuj.pl header.s=s1 header.b=AbC; "
    "spf=pass (google.com: domain of bounce@mail.pracuj.pl designates 1.2.3.4 as permitted "
    "sender) smtp.mailfrom=bounce@mail.pracuj.pl; "
    "dmarc=pass (p=REJECT sp=REJECT dis=NONE) header.from=pracuj.pl"
)


def letter(to: str, subject: str, html: str, sender: str = "alerts@upwork.com", **headers) -> bytes:
    message = EmailMessage()
    message["From"] = sender
    message["To"] = to
    message["Subject"] = subject
    message["Date"] = "Thu, 29 Oct 2026 10:00:00 +0000"
    for name, value in headers.items():
        message[name.replace("_", "-")] = value
    message.set_content("plain version")
    message.add_alternative(html, subtype="html")
    return message.as_bytes()


ALERT = """<html><body>
<p>New jobs for "video editor"</p>
<a href="https://www.upwork.com/jobs/~01abc">Podcast Video Editor needed</a>
<p>Edit weekly podcast episodes. $30/episode.</p>
<a href="https://www.upwork.com/jobs/~02def">Reels editor for a coach</a>
<a href="https://www.upwork.com/settings">Notification settings</a>
<a href="mailto:x@y.z">mail us</a>
</body></html>"""


def test_personal_address_carries_a_token():
    token = new_token()
    assert len(token) == 10
    assert BOX.personal(token) == f"jobradar.inbox+{token}@gmail.com"
    assert not MailConfig("imap.gmail.com", "", "").enabled


def test_a_forwarded_alert_is_read_with_its_links():
    # Forwarding keeps the user's own address in To; the bot's is in Delivered-To
    raw = letter(
        "me@gmail.com", "New jobs", ALERT, Delivered_To="jobradar.inbox+0a1b2c3d4e@gmail.com"
    )
    read = read_letter(raw)
    assert read.token == "0a1b2c3d4e"
    assert read.sender == "upwork.com"
    assert read.received == datetime(2026, 10, 29, 10, tzinfo=UTC)
    assert "Edit weekly podcast episodes" in read.text
    assert read.links[:2] == [
        ("https://www.upwork.com/jobs/~01abc", "Podcast Video Editor needed"),
        ("https://www.upwork.com/jobs/~02def", "Reels editor for a coach"),
    ]
    assert all(url.startswith("https://") for url, _ in read.links)  # no mailto


def test_a_letter_to_the_box_itself_is_for_everyone():
    assert read_letter(letter("jobradar.inbox@gmail.com", "Hi", "<p>hi</p>")).token is None


def test_gmail_vouches_for_a_genuine_sender():
    raw = letter(
        "jobradar.inbox@gmail.com",
        "Oferty",
        ALERT,
        "oferty@pracuj.pl",
        Authentication_Results=GENUINE,
    )
    assert read_letter(raw).verified


def test_a_site_may_sign_for_its_subdomains():
    signed = "mx.google.com; dkim=pass header.i=@useme.com header.s=k1 header.b=x; spf=pass"
    raw = letter(
        "jobradar.inbox@gmail.com",
        "Zlecenia",
        ALERT,
        "news@mail.useme.com",
        Authentication_Results=signed,
    )
    assert read_letter(raw).verified


def test_a_forged_sender_is_not_verified():
    # Anyone can write "From: pracuj.pl"; the signature is the spammer's own domain
    forged = (
        "mx.google.com; dkim=pass header.i=@evil.example header.s=s header.b=x; "
        "spf=pass smtp.mailfrom=x@evil.example; dmarc=fail (p=NONE) header.from=pracuj.pl"
    )
    raw = letter(
        "jobradar.inbox@gmail.com",
        "Oferty",
        ALERT,
        "oferty@pracuj.pl",
        Authentication_Results=forged,
    )
    assert not read_letter(raw).verified


def test_only_gmails_own_check_on_top_counts():
    # The sender wrote a "pass" header itself; Gmail's own, added on top, says it failed
    raw = letter(
        "jobradar.inbox@gmail.com",
        "Oferty",
        ALERT,
        "oferty@pracuj.pl",
        Authentication_Results=GENUINE,
    )
    gmail = b"Authentication-Results: mx.google.com; dmarc=fail header.from=pracuj.pl\r\n"
    assert not read_letter(gmail + raw).verified
    assert not read_letter(letter("jobradar.inbox@gmail.com", "Oferty", ALERT)).verified
    other = GENUINE.replace("mx.google.com", "mail.evil.example")
    raw = letter(
        "jobradar.inbox@gmail.com",
        "Oferty",
        ALERT,
        "oferty@pracuj.pl",
        Authentication_Results=other,
    )
    assert not read_letter(raw).verified


def test_only_listed_sites_and_their_subdomains_count():
    box = MailConfig("imap.gmail.com", "jobradar.inbox@gmail.com", "pw", ("pracuj.pl", "useme.com"))
    assert box.site("pracuj.pl") == "pracuj.pl"
    assert box.site("mail.pracuj.pl") == "pracuj.pl"
    assert box.site("notpracuj.pl") is None
    assert box.site("pracuj.pl.evil.example") is None


def test_the_listed_sites_come_from_env_or_the_built_in_list():
    listed = JobRadarSettings.model_construct(mail_senders_raw=" Pracuj.pl, @useme.com,,pracuj.pl")
    assert listed.mail_senders == ("pracuj.pl", "useme.com")
    assert JobRadarSettings.model_construct(mail_senders_raw="").mail_senders == MAIL_SENDERS


def test_a_subscription_confirmation_is_recognized():
    raw = letter(
        "jobradar.inbox@gmail.com",
        "Potwierdź subskrypcję powiadomień",
        '<a href="https://www.pracuj.pl/">Pracuj.pl</a>'
        '<a href="https://www.pracuj.pl/alerts/confirm?t=abc">Potwierdzam</a>',
        sender="noreply@pracuj.pl",
    )
    assert confirmation_links(read_letter(raw)) == ["https://www.pracuj.pl/alerts/confirm?t=abc"]


def test_a_job_alert_is_not_a_confirmation():
    # Upwork marks clients "Payment verified": a job card, not a confirmation
    raw = letter(
        "jobradar.inbox@gmail.com",
        "New jobs for video editor",
        '<a href="https://www.upwork.com/jobs/~01abc">Video editor · Payment verified</a>',
    )
    assert confirmation_links(read_letter(raw)) is None


def test_the_ai_can_only_pick_links_that_are_in_the_letter():
    links = read_letter(letter("jobradar.inbox+0a1b2c3d4e@gmail.com", "New jobs", ALERT)).links
    answer = {
        "jobs": [
            {"title": "Podcast Video Editor", "link": 0, "details": "$30/episode"},
            {"title": "Made up", "link": 99, "details": "a link that isn't there"},
            {"title": "Same job again", "link": 0, "details": "duplicate"},
        ]
    }
    jobs = letter_jobs(answer, links)
    assert [(j.url, j.title) for j in jobs] == [
        ("https://www.upwork.com/jobs/~01abc", "Same job again")
    ]
    assert "[0] Podcast Video Editor needed" in letter_prompt("New jobs", "text", links)


def test_gmail_forwarding_confirmation_is_passed_on():
    raw = letter(
        "jobradar.inbox+0a1b2c3d4e@gmail.com",
        "(#123456789) Gmail Forwarding Confirmation - Receive Mail from me@gmail.com",
        "<p>Confirmation code: 123456789</p>"
        '<a href="https://mail-settings.google.com/mail/vf-abc">confirm</a>',
        sender="forwarding-noreply@google.com",
    )
    assert gmail_confirmation(read_letter(raw)) == (
        "123456789",
        "https://mail-settings.google.com/mail/vf-abc",
    )


def test_a_fake_confirmation_from_elsewhere_is_not_trusted():
    raw = letter(
        "jobradar.inbox+0a1b2c3d4e@gmail.com",
        "(#1) Gmail Forwarding Confirmation",
        '<a href="https://evil.example/login">confirm</a>',
        sender="noreply@evil.example",
    )
    assert gmail_confirmation(read_letter(raw)) is None


def test_a_letter_in_an_unknown_charset_is_still_read():
    raw = (
        b"From: alerts@upwork.com\r\nTo: jobradar.inbox+0a1b2c3d4e@gmail.com\r\n"
        b"Subject: New jobs\r\nDate: Thu, 29 Oct 2026 10:00:00 +0000\r\nMIME-Version: 1.0\r\n"
        b'Content-Type: text/html; charset="x-bogus"\r\n\r\n'
        b'<a href="https://www.upwork.com/jobs/~01abc">Video editor</a>'
    )
    assert read_letter(raw).links == [("https://www.upwork.com/jobs/~01abc", "Video editor")]


def test_bare_links_are_shown_to_the_ai_by_their_address():
    links = [("https://ex.com/jobs/1", ""), ("https://ex.com/unsubscribe", "")]
    prompt = letter_prompt("Jobs", "text", links)
    assert "[0] https://ex.com/jobs/1" in prompt
    assert "[1] https://ex.com/unsubscribe" in prompt
