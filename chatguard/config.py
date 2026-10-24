from pydantic import Field, SecretStr, field_validator

from shared.config import CommonSettings


class ChatGuardSettings(CommonSettings):
    token: SecretStr = Field(validation_alias="CHATGUARD_TOKEN")
    database_url: str = Field(validation_alias="CHATGUARD_DATABASE_URL")
    # Empty key = rules only, no AI
    anthropic_api_key: SecretStr = Field(SecretStr(""), validation_alias="ANTHROPIC_API_KEY")
    # Cost guard: AI checks per chat per day; beyond that the chat falls back to rules
    ai_daily_limit: int = Field(300, validation_alias="CHATGUARD_AI_DAILY_LIMIT")

    @field_validator("token")
    @classmethod
    def token_not_empty(cls, v: SecretStr) -> SecretStr:
        if not v.get_secret_value():
            raise ValueError("CHATGUARD_TOKEN is empty: put the token from @BotFather into .env")
        return v
