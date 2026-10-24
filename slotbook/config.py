from pydantic import Field, SecretStr, field_validator

from shared.config import CommonSettings, parse_ids


class SlotBookSettings(CommonSettings):
    token: SecretStr = Field(validation_alias="SLOTBOOK_TOKEN")
    database_url: str = Field(validation_alias="SLOTBOOK_DATABASE_URL")
    admin_ids_raw: str = Field("", validation_alias="SLOTBOOK_ADMIN_IDS")
    # Prices are shown in the master's currency whatever language the client uses
    currency: str = Field("₴", validation_alias="SLOTBOOK_CURRENCY")

    @field_validator("token")
    @classmethod
    def token_not_empty(cls, v: SecretStr) -> SecretStr:
        if not v.get_secret_value():
            raise ValueError("SLOTBOOK_TOKEN is empty: put the token from @BotFather into .env")
        return v

    @property
    def admin_ids(self) -> set[int]:
        return parse_ids(self.admin_ids_raw)
