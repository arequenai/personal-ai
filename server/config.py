from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mcp_secret: str
    railway_api_base: str = "https://garmin-sync-production-ec24.up.railway.app"
    railway_api_key: str = ""  # X-API-Key del aggregator garmin-sync; vacío = sin header
    finance_sync_base_url: str = "http://localhost:8000"
    port: int = 8000

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
