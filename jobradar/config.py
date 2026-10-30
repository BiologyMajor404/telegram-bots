"""JobRadar settings from .env and the Free/Pro plan limits."""

from dataclasses import dataclass

from pydantic import Field, SecretStr, field_validator

from jobradar.mail import MailConfig
from shared.config import CommonSettings, parse_ids


@dataclass(frozen=True)
class Plan:
    cards: int  # job cards a day
    sources: int  # own sources added by link
    searches: int  # kinds of work to look for, in the user's own words
    own_checks: int  # AI checks a day of jobs that only this user's sources found


@dataclass(frozen=True)
class Plans:
    """Free vs Pro. Pro is sized so its worst month of AI costs stays below what
    Telegram pays out for one month of the subscription."""

    free: Plan
    pro: Plan
    pro_price_stars: int
    base_usd: float  # monthly AI budget for everyone, Free users can't spend more
    usd_per_pro: float  # added to the monthly budget by each paying subscriber


class JobRadarSettings(CommonSettings):
    token: SecretStr = Field(validation_alias="JOBRADAR_TOKEN")
    database_url: str = Field(validation_alias="JOBRADAR_DATABASE_URL")
    anthropic_api_key: SecretStr = Field(validation_alias="ANTHROPIC_API_KEY")
    # Who may subscribe, e.g. "123,456"; empty = anyone
    allowed_ids_raw: str = Field("", validation_alias="JOBRADAR_ALLOWED_IDS")
    # Owners: Pro for free and the AI spend in /status
    admin_ids_raw: str = Field("", validation_alias="JOBRADAR_ADMIN_IDS")
    poll_minutes: int = Field(10, ge=1, validation_alias="JOBRADAR_POLL_MINUTES")

    free_cards: int = Field(5, ge=0, validation_alias="JOBRADAR_FREE_CARDS")
    free_sources: int = Field(1, ge=0, validation_alias="JOBRADAR_FREE_SOURCES")
    free_searches: int = Field(3, ge=0, validation_alias="JOBRADAR_FREE_SEARCHES")
    free_own_checks: int = Field(15, ge=0, validation_alias="JOBRADAR_FREE_OWN_CHECKS")
    pro_cards: int = Field(20, ge=0, validation_alias="JOBRADAR_PRO_CARDS")
    pro_sources: int = Field(10, ge=0, validation_alias="JOBRADAR_PRO_SOURCES")
    pro_searches: int = Field(10, ge=0, validation_alias="JOBRADAR_PRO_SEARCHES")
    pro_own_checks: int = Field(60, ge=0, validation_alias="JOBRADAR_PRO_OWN_CHECKS")
    pro_price_stars: int = Field(250, ge=1, le=10_000, validation_alias="JOBRADAR_PRO_PRICE_STARS")
    # Cost ceiling in USD a month, spent evenly: each day gets its share
    ai_monthly_usd: float = Field(3.0, ge=0, validation_alias="JOBRADAR_AI_MONTHLY_USD")
    ai_usd_per_pro: float = Field(2.5, ge=0, validation_alias="JOBRADAR_AI_USD_PER_PRO")
    # A second fuse, in case token prices or counts are ever off: AI checks per day
    ai_daily_limit: int = Field(400, ge=0, validation_alias="JOBRADAR_AI_DAILY_LIMIT")
    # Shown in /paysupport, e.g. @your_username; empty = no contact line
    support_contact: str = Field("", validation_alias="JOBRADAR_SUPPORT_CONTACT")

    # The bot's own mailbox for job alert emails; empty = the feature is off
    mail_address: str = Field("", validation_alias="JOBRADAR_MAIL_ADDRESS")
    mail_password: SecretStr = Field(SecretStr(""), validation_alias="JOBRADAR_MAIL_PASSWORD")
    mail_imap_host: str = Field("imap.gmail.com", validation_alias="JOBRADAR_MAIL_IMAP_HOST")
    # Personal API token from your Freelancehunt profile; empty = Freelancehunt is off
    freelancehunt_token: SecretStr = Field(SecretStr(""), validation_alias="FREELANCEHUNT_TOKEN")
    # Public Telegram channels with job posts, without @, comma-separated
    channels_raw: str = Field(
        "theyseeku,digital_jobster,bazuwork,zapwork", validation_alias="JOBRADAR_TG_CHANNELS"
    )

    @field_validator("token", "anthropic_api_key")
    @classmethod
    def not_empty(cls, v: SecretStr) -> SecretStr:
        if not v.get_secret_value():
            raise ValueError("JOBRADAR_TOKEN and ANTHROPIC_API_KEY must be set in .env")
        return v

    @property
    def allowed_ids(self) -> set[int]:
        return parse_ids(self.allowed_ids_raw)

    @property
    def admin_ids(self) -> set[int]:
        return parse_ids(self.admin_ids_raw)

    @property
    def channels(self) -> list[str]:
        return [c.strip().lstrip("@").lower() for c in self.channels_raw.split(",") if c.strip()]

    @property
    def mail(self) -> MailConfig:
        return MailConfig(
            self.mail_imap_host, self.mail_address.strip(), self.mail_password.get_secret_value()
        )

    @property
    def plans(self) -> Plans:
        return Plans(
            free=Plan(self.free_cards, self.free_sources, self.free_searches, self.free_own_checks),
            pro=Plan(self.pro_cards, self.pro_sources, self.pro_searches, self.pro_own_checks),
            pro_price_stars=self.pro_price_stars,
            base_usd=self.ai_monthly_usd,
            usd_per_pro=self.ai_usd_per_pro,
        )
