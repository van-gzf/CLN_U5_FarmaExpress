from datetime import datetime, timedelta, timezone

from src.security import can_cancel


def test_owner_within_24h():
    now = datetime.now(timezone.utc)
    assert can_cancel("NEW", 1, 1, False, now - timedelta(hours=1), now)

def test_stranger_denied():
    now = datetime.now(timezone.utc)
    assert not can_cancel("NEW", 1, 2, False, now, now)

def test_shipped_denied_even_admin():
    now = datetime.now(timezone.utc)
    assert not can_cancel("SHIPPED", 1, 1, True, now, now)

def test_expired_denied():
    now = datetime.now(timezone.utc)
    assert not can_cancel("NEW", 1, 1, False, now - timedelta(hours=25), now)


# --- E6: fechas fijas y 'now' explicito (sin resultados variables) ---
NOW = datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc)


def test_admin_can_cancel_new_order_of_other_user():
    assert can_cancel("NEW", 1, 99, True, NOW - timedelta(hours=48), NOW)


def test_owner_exactly_24h_is_denied():
    assert not can_cancel("NEW", 1, 1, False, NOW - timedelta(hours=24), NOW)


def test_owner_just_under_24h_is_allowed():
    assert can_cancel("NEW", 1, 1, False, NOW - timedelta(hours=23, minutes=59), NOW)
