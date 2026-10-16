from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ClinicDesk API"
    app_version: str = "1.0.0"
    database_url: str = "postgresql+psycopg://clinicdesk:clinicdesk@localhost:5432/clinicdesk"
    # comma separated list, only matters when the UI is served from another origin (vite dev server)
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
