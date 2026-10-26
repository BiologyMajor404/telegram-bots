"""ChatGuard AI settings from .env and the Free/Pro plan limits."""

from dataclasses import dataclass

from pydantic import Field, SecretStr, field_validator

from shared.config import CommonSettings


@dataclass(frozen=True)
class Plans:
    """Free vs Pro: how many AI checks a chat gets per day and what Pro costs."""

    free_limit: int
    pro_limit: int
    pro_price_stars: int
    global_limit: int  # AI checks per day for the whole bot


class ChatGuardSettings(CommonSettings):
    token: SecretStr = Field(validation_alias="CHATGUARD_TOKEN")
    database_url: str = Field(validation_alias="CHATGUARD_DATABASE_URL")
    # Empty key = rules only, no AI
    anthropic_api_key: SecretStr = Field(SecretStr(""), validation_alias="ANTHROPIC_API_KEY")
    # Cost guard: AI checks per chat per day; beyond that the chat falls back to rules
    ai_limit_free: int = Field(50, validation_alias="CHATGUARD_AI_LIMIT_FREE")
    ai_limit_pro: int = Field(300, validation_alias="CHATGUARD_AI_LIMIT_PRO")
    pro_price_stars: int = Field(250, validation_alias="CHATGUARD_PRO_PRICE_STARS")
    # Ceiling for all chats together, so many chats (or many fake ones) can't run up the bill
    ai_limit_global: int = Field(1500, validation_alias="CHATGUARD_AI_LIMIT_GLOBAL")
    # Shown in /paysupport, e.g. @your_username; empty = no contact line
    support_contact: str = Field("", validation_alias="CHATGUARD_SUPPORT_CONTACT")

    @field_validator("token")
    @classmethod
    def token_not_empty(cls, v: SecretStr) -> SecretStr:
        if not v.get_secret_value():
            raise ValueError("CHATGUARD_TOKEN is empty: put the token from @BotFather into .env")
        return v

    @property
    def plans(self) -> Plans:
        return Plans(
            self.ai_limit_free, self.ai_limit_pro, self.pro_price_stars, self.ai_limit_global
        )
