"""Tests untuk modules_client/logger.py"""

import re
import pytest

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def clear_log_data():
    """Bersihkan log_data sebelum dan sesudah setiap test."""
    from modules_client.logger import log_data
    log_data.clear()
    yield
    log_data.clear()


def test_add_log_appends_entry():
    """add_log harus append entry dengan speaker, message, dan timestamp yang benar."""
    from modules_client.logger import add_log, get_log

    add_log("System", "App started")
    entries = get_log()

    assert len(entries) == 1
    assert entries[0]["speaker"] == "System"
    assert entries[0]["message"] == "App started"
    assert "timestamp" in entries[0]


def test_add_log_multiple():
    """3 pemanggilan add_log harus menghasilkan 3 entry di log."""
    from modules_client.logger import add_log, get_log

    add_log("System", "First message")
    add_log("User", "Second message")
    add_log("AI", "Third message")

    assert len(get_log()) == 3


def test_get_log_returns_list():
    """get_log harus mengembalikan objek bertipe list."""
    from modules_client.logger import get_log

    result = get_log()
    assert isinstance(result, list)


def test_log_entry_has_timestamp_format():
    """Timestamp entry harus sesuai format YYYY-MM-DD HH:MM:SS."""
    from modules_client.logger import add_log, get_log

    add_log("System", "Timestamp check")
    entry = get_log()[0]

    timestamp_pattern = r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}'
    assert re.match(timestamp_pattern, entry["timestamp"]), (
        f"Timestamp '{entry['timestamp']}' tidak sesuai format YYYY-MM-DD HH:MM:SS"
    )


def test_logger_class_methods():
    """Logger class harus punya info/error/warning/debug yang tidak crash."""
    from modules_client.logger import Logger

    logger = Logger("Test")

    # Semua method harus bisa dipanggil tanpa exception
    logger.info("info message")
    logger.error("error message")
    logger.warning("warning message")
    logger.debug("debug message")
