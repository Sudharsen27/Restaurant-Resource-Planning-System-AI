"""Restaurant schema validation — empty optional fields must not 422."""

from app.schemas.restaurant import RestaurantCreate, RestaurantUpdate


def test_create_accepts_blank_email_as_none():
    payload = RestaurantCreate(name="Cafe One", code="C1", email="")
    assert payload.email is None


def test_create_accepts_whitespace_email_as_none():
    payload = RestaurantCreate(name="Cafe Two", code="C2", email="   ")
    assert payload.email is None


def test_create_keeps_valid_email():
    payload = RestaurantCreate(name="Cafe Three", code="C3", email="ops@example.com")
    assert str(payload.email) == "ops@example.com"


def test_update_accepts_blank_email_as_none():
    payload = RestaurantUpdate(email="")
    assert payload.email is None
