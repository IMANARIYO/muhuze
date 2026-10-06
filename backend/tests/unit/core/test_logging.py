import json
import logging
import sys

import pytest

from app.core.logging import (
    REDACTED,
    JSONFormatter,
    RequestContextFilter,
    TextFormatter,
    configure_logging,
    is_sensitive_key,
    request_id_var,
)


def make_record(msg: str = "hello", exc_info=None, **extra) -> logging.LogRecord:
    record = logging.LogRecord(
        name="app.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg=msg,
        args=(),
        exc_info=exc_info,
    )
    for key, value in extra.items():
        setattr(record, key, value)
    return record


def test_filter_uses_dash_outside_a_request() -> None:
    record = make_record()
    assert RequestContextFilter().filter(record) is True
    assert record.request_id == "-"


def test_filter_stamps_current_request_id() -> None:
    token = request_id_var.set("req-123")
    try:
        record = make_record()
        RequestContextFilter().filter(record)
        assert record.request_id == "req-123"
    finally:
        request_id_var.reset(token)


@pytest.mark.parametrize(
    "key",
    [
        "password",
        "new_password",
        "access_token",
        "Authorization",
        "api_key",
        "otp",
        "pin",
        "account_number",
        "webhook-secret",
    ],
)
def test_sensitive_keys_are_detected(key: str) -> None:
    assert is_sensitive_key(key)


@pytest.mark.parametrize("key", ["shipping_fee", "order_id", "spinner", "path", "status_code"])
def test_ordinary_keys_are_not_redacted(key: str) -> None:
    assert not is_sensitive_key(key)


def test_uvicorn_color_message_is_not_rendered() -> None:
    record = make_record("Started server process", color_message="\x1b[36mStarted\x1b[0m")
    RequestContextFilter().filter(record)
    assert "color_message" not in TextFormatter().format(record)
    assert "color_message" not in json.loads(JSONFormatter().format(record))


def test_filter_redacts_sensitive_extras_only() -> None:
    record = make_record(password="hunter2", order_id="o-1")
    RequestContextFilter().filter(record)
    assert record.password == REDACTED
    assert record.order_id == "o-1"


def test_json_formatter_emits_one_object_with_context_and_extras() -> None:
    record = make_record("order created", order_id="o-1")
    RequestContextFilter().filter(record)
    payload = json.loads(JSONFormatter().format(record))
    assert payload["message"] == "order created"
    assert payload["level"] == "INFO"
    assert payload["logger"] == "app.test"
    assert payload["request_id"] == "-"
    assert payload["order_id"] == "o-1"
    assert payload["timestamp"].endswith("+00:00")


def test_json_formatter_includes_exception() -> None:
    try:
        raise RuntimeError("boom")
    except RuntimeError:
        record = make_record("failed", exc_info=sys.exc_info())
    payload = json.loads(JSONFormatter().format(record))
    assert "RuntimeError: boom" in payload["exception"]


def test_text_formatter_appends_extras() -> None:
    record = make_record("request completed", status_code=200)
    RequestContextFilter().filter(record)
    line = TextFormatter().format(record)
    assert "request completed | status_code=200" in line
    assert "[-]" in line


def _our_handlers() -> list[logging.Handler]:
    return [h for h in logging.getLogger().handlers if getattr(h, "_muhuze_handler", False)]


def test_configure_logging_is_idempotent_and_keeps_foreign_handlers(make_settings) -> None:
    root = logging.getLogger()
    foreign = logging.NullHandler()
    root.addHandler(foreign)
    try:
        configure_logging(make_settings())
        configure_logging(make_settings())
        assert len(_our_handlers()) == 1
        assert foreign in root.handlers
    finally:
        root.removeHandler(foreign)


def test_configure_logging_uses_json_in_production(make_settings) -> None:
    configure_logging(make_settings(environment="production"))
    try:
        (handler,) = _our_handlers()
        assert isinstance(handler.formatter, JSONFormatter)
        assert logging.getLogger().level == logging.INFO
        assert logging.getLogger("uvicorn.access").disabled
    finally:
        configure_logging(make_settings())


@pytest.mark.parametrize(
    ("environment", "level", "fmt"),
    [
        ("development", "DEBUG", "text"),
        ("test", "INFO", "text"),
        ("staging", "INFO", "json"),
        ("production", "INFO", "json"),
    ],
)
def test_log_defaults_follow_environment(
    make_settings, environment: str, level: str, fmt: str
) -> None:
    settings = make_settings(environment=environment)
    assert settings.effective_log_level == level
    assert settings.effective_log_format == fmt


def test_explicit_log_settings_override_defaults_and_empty_means_unset(make_settings) -> None:
    settings = make_settings(environment="production", log_level="debug", log_format="TEXT")
    assert settings.effective_log_level == "DEBUG"
    assert settings.effective_log_format == "text"
    unset = make_settings(environment="production", log_level="", log_format="")
    assert unset.effective_log_level == "INFO"
    assert unset.effective_log_format == "json"
