"""SQLModel persistence operations for application settings."""

from sqlmodel import col, select

from termkeeper.infrastructure.connection import get_session
from termkeeper.infrastructure.sqlite_utils import now
from termkeeper.infrastructure.tables import AppSetting


def get_setting(key: str) -> AppSetting | None:
    with get_session() as session:
        return session.get(AppSetting, key)


def set_setting(key: str, value: str) -> AppSetting:
    with get_session() as session:
        setting = session.get(AppSetting, key)
        if setting is None:
            setting = AppSetting(key=key, value=value, updated_at=now())
        else:
            setting.value = value
            setting.updated_at = now()
        session.add(setting)
        session.commit()
        session.refresh(setting)
        return setting


def list_settings() -> list[AppSetting]:
    statement = select(AppSetting).order_by(col(AppSetting.key))
    with get_session() as session:
        return list(session.exec(statement).all())
