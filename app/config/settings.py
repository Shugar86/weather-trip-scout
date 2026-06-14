from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Optional so the pipeline can run in --dry-run mode without a bot.
    # Required only when actually sending a report; validated at send time.
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None
    open_weather_api_key: str | None = None
    mapbox_token: str | None = None
