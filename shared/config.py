from zoneinfo import ZoneInfo

from pydantic_settings import BaseSettings, SettingsConfigDict


class CommonSettings(BaseSettings):
    """Settings every bot needs. Bot-specific settings subclass this."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    timezone: str = "Europe/Moscow"
    log_level: str = "INFO"
    redis_url: str = ""

    @property
    def tz(self) -> ZoneInfo:
        return ZoneInfo(self.timezone)


def parse_ids(raw: str) -> set[int]:
    """'123, 456' -> {123, 456}"""
    return {int(part) for part in raw.replace(" ", "").split(",") if part}
