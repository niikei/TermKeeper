"""Persistence operations for the single local user profile."""

from sqlmodel import Session, select

from termkeeper.infrastructure.tables import UserProfile, utc_now


def get_profile(session: Session) -> UserProfile | None:
    return session.exec(select(UserProfile).limit(1)).first()


def get_or_create_profile(session: Session) -> UserProfile:
    profile = get_profile(session)
    if profile is None:
        profile = UserProfile()
        session.add(profile)
        session.flush()
    return profile


def set_value(session: Session, key: str, value: str) -> UserProfile:
    profile = get_or_create_profile(session)
    setattr(profile, _field(key), value)
    profile.updated_at = utc_now()
    session.add(profile)
    return profile


def unset_value(session: Session, key: str) -> UserProfile:
    profile = get_or_create_profile(session)
    setattr(profile, _field(key), None)
    profile.updated_at = utc_now()
    session.add(profile)
    return profile


def as_config(profile: UserProfile | None) -> dict[str, str]:
    if profile is None:
        return {}
    values = {"user.name": profile.name, "user.email": profile.email}
    return {key: value for key, value in values.items() if value is not None}


def _field(key: str) -> str:
    return {"user.name": "name", "user.email": "email"}[key]
