"""SplitMates settings from .env."""

from pydantic import Field, SecretStr, field_validator

from shared.config import CommonSettings


class SplitMateSettings(CommonSettings):
    token: SecretStr = Field(validation_alias="SPLITMATE_TOKEN")
    database_url: str = Field(validation_alias="SPLITMATE_DATABASE_URL")

    @field_validator("token")
    @classmethod
    def token_not_empty(cls, v: SecretStr) -> SecretStr:
        if not v.get_secret_value():
            raise ValueError("SPLITMATE_TOKEN is empty: put the token from @BotFather into .env")
        return v
