import logging

import pytest

from app.core import notifications
from app.core.config import settings


async def test_send_email_logs_when_smtp_not_configured(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setattr(settings, "smtp_host", None)
    with caplog.at_level(logging.INFO):
        await notifications.send_email(
            to="a@example.com", subject="Hi", body="Body text"
        )
    assert "logging only" in caplog.text
    assert "a@example.com" in caplog.text


async def test_send_email_sends_via_smtp_when_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "smtp_host", "smtp.example.com")
    monkeypatch.setattr(settings, "smtp_port", 2525)
    monkeypatch.setattr(settings, "smtp_username", "smtp-user")
    monkeypatch.setattr(settings, "smtp_password", "smtp-pass")
    monkeypatch.setattr(settings, "smtp_from_email", "noreply@muhuze.com")
    monkeypatch.setattr(settings, "smtp_use_tls", True)

    captured = {}

    async def fake_send(message, *, hostname, port, username, password, start_tls):
        captured["to"] = message["To"]
        captured["from"] = message["From"]
        captured["subject"] = message["Subject"]
        captured["body"] = message.get_content().strip()
        captured["hostname"] = hostname
        captured["port"] = port
        captured["username"] = username
        captured["password"] = password
        captured["start_tls"] = start_tls

    monkeypatch.setattr(notifications.aiosmtplib, "send", fake_send)

    await notifications.send_email(
        to="someone@example.com", subject="Hello", body="World"
    )

    assert captured == {
        "to": "someone@example.com",
        "from": "noreply@muhuze.com",
        "subject": "Hello",
        "body": "World",
        "hostname": "smtp.example.com",
        "port": 2525,
        "username": "smtp-user",
        "password": "smtp-pass",
        "start_tls": True,
    }


async def test_send_email_falls_back_to_username_when_from_email_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "smtp_host", "smtp.example.com")
    monkeypatch.setattr(settings, "smtp_username", "smtp-user@example.com")
    monkeypatch.setattr(settings, "smtp_from_email", None)

    captured = {}

    async def fake_send(message, **_kwargs):
        captured["from"] = message["From"]

    monkeypatch.setattr(notifications.aiosmtplib, "send", fake_send)

    await notifications.send_email(to="x@example.com", subject="s", body="b")

    assert captured["from"] == "smtp-user@example.com"
