from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    frontend_url: str = "http://localhost:5173"
    allowed_origins: str = ""

    model_config = {"env_file": ".env"}

    @property
    def cors_origins(self) -> list[str]:
        origins = [self.frontend_url]
        if self.allowed_origins:
            origins.extend(o.strip() for o in self.allowed_origins.split(",") if o.strip())
        return origins


settings = Settings()
