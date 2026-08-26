import logging

from app.core.logging import RequestIdFilter, get_logger, request_id_var


def make_record() -> logging.LogRecord:
    return logging.LogRecord(
        name="test", level=logging.INFO, pathname=__file__, lineno=1, msg="hi", args=(), exc_info=None
    )


def test_filter_defaults_to_dash_outside_request_context() -> None:
    record = make_record()
    assert RequestIdFilter().filter(record) is True
    assert record.request_id == "-"


def test_filter_picks_up_context_var() -> None:
    token = request_id_var.set("abc-123")
    try:
        record = make_record()
        RequestIdFilter().filter(record)
        assert record.request_id == "abc-123"
    finally:
        request_id_var.reset(token)


def test_get_logger_returns_named_logger() -> None:
    logger = get_logger("app.modules.auth.service")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "app.modules.auth.service"
