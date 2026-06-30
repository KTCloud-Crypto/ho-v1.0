from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    upbit_access_key: str
    upbit_secret_key: str
    telegram_bot_token: str
    telegram_chat_id: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
