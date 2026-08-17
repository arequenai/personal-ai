from urllib.parse import urlparse

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mcp_secret: str
    railway_api_base: str = "https://garmin-sync-production-ec24.up.railway.app"
    railway_api_key: str = ""  # X-API-Key del aggregator garmin-sync; vacío = sin header
    finance_sync_base_url: str = "http://localhost:8000"
    port: int = 8000

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def finance_sync_is_localhost(self) -> bool:
        """True si finance_sync_base_url apunta al propio host (default sin configurar).

        El servidor escucha en el puerto 8000: si FINANCE_SYNC_BASE_URL no está
        definida en el entorno, las 8 tools finance_* se llaman a sí mismas y
        devuelven 404. Este flag hace ese estado visible en /health y en los logs
        de arranque.
        """
        host = urlparse(self.finance_sync_base_url).hostname
        return host in (None, "localhost", "127.0.0.1", "0.0.0.0", "::1")


settings = Settings()
