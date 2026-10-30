"""JobRadar: job alert emails sent on to a subscriber's personal address."""

from datetime import UTC, datetime
from email.message import EmailMessage

from jobradar.ai import letter_jobs, letter_prompt
from jobradar.mail import MailConfig, gmail_confirmation, new_token, read_letter

BOX = MailConfig("imap.gmail.com", "jobradar.inbox@gmail.com", "app-password")


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


def test_letters_to_other_addresses_are_ignored():
    assert read_letter(letter("jobradar.inbox@gmail.com", "Hi", "<p>hi</p>")) is None


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
