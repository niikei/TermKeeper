import pytest

from termkeeper.application import NotFoundError, TermKeeperService, ValidationError


def test_user_configuration_round_trip_and_validation() -> None:
    service = TermKeeperService()
    with pytest.raises(NotFoundError):
        service.get_config("user.name")

    name = service.set_config("user.name", " Taro Yamada ")
    email = service.set_config("user.email", "taro@example.com")

    assert name["value"] == "Taro Yamada"
    assert service.get_config("user.email") == email
    assert service.list_config() == {
        "user.email": "taro@example.com",
        "user.name": "Taro Yamada",
    }
    with pytest.raises(ValidationError):
        service.get_config("user.name.missing")
    with pytest.raises(ValidationError):
        service.set_config("user.email", "invalid")
    with pytest.raises(ValidationError):
        service.set_config("user.name", " ")
