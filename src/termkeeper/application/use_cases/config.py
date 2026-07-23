"""User configuration use cases."""

from termkeeper.application.errors import NotFoundError, ValidationError
from termkeeper.infrastructure.repositories import settings_repository
from termkeeper.infrastructure.unit_of_work import UnitOfWork


class ConfigUseCases:
    def set_config(self, key: str, value: str) -> dict[str, str]:
        _validate_config(key, value)
        with UnitOfWork() as uow:
            profile = settings_repository.set_value(uow.session, key, value.strip())
            uow.commit()
            return {"key": key, "value": settings_repository.as_config(profile)[key]}

    def get_config(self, key: str) -> dict[str, str]:
        _validate_config_key(key)
        with UnitOfWork() as uow:
            config = settings_repository.as_config(settings_repository.get_profile(uow.session))
            if key not in config:
                message = f"Configuration '{key}' was not found."
                raise NotFoundError(message)
            return {"key": key, "value": config[key]}

    def list_config(self) -> dict[str, str]:
        with UnitOfWork() as uow:
            return settings_repository.as_config(settings_repository.get_profile(uow.session))

    def unset_config(self, key: str) -> dict[str, str]:
        _validate_config_key(key)
        with UnitOfWork() as uow:
            profile = settings_repository.unset_value(uow.session, key)
            uow.commit()
            return settings_repository.as_config(profile)


def _validate_config(key: str, value: str) -> None:
    _validate_config_key(key)
    if not value.strip():
        message = f"Configuration '{key}' must not be empty."
        raise ValidationError(message)
    if key == "user.email" and ("@" not in value or value.startswith("@") or value.endswith("@")):
        message = "user.email must be a valid email address."
        raise ValidationError(message)


def _validate_config_key(key: str) -> None:
    if key not in {"user.name", "user.email"}:
        message = f"Unsupported configuration key: {key}"
        raise ValidationError(message)
