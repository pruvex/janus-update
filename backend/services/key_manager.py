from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: SecretStr | None = None
    google_api_key: SecretStr | None = None
    # Add other API keys here as needed


settings = Settings()


def get_api_key(provider: str) -> str | None:
    """Lädt den API-Key für einen gegebenen Anbieter aus Umgebungsvariablen oder .env-Datei."""
    if provider.lower() == "openai":
        return settings.openai_api_key.get_secret_value() if settings.openai_api_key else None
    elif provider.lower() == "google":
        return settings.google_api_key.get_secret_value() if settings.google_api_key else None
    # Add other providers here
    return None
