from functools import cached_property

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration read only from environment variables or a local .env file."""

    model_config = SettingsConfigDict(
        env_prefix="CLOUDTASK_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = "development"
    database_url: str = ""
    rabbitmq_url: str = ""
    s3_endpoint_url: str = ""
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_bucket: str = "cloudtask"
    upload_max_bytes: int = 20 * 1024 * 1024
    max_attempts: int = 3
    retry_delay_seconds: int = 10
    s3_max_attempts: int = 3
    s3_connect_timeout_seconds: int = 3
    s3_read_timeout_seconds: int = 10
    cors_origins: str = "http://localhost:3000"
    metrics_port: int = 8001
    jwt_secret: str = ""
    jwt_expiry_minutes: int = 480
    bootstrap_user_email: str = ""
    bootstrap_user_password: str = ""
    rate_limit_requests: int = 120
    rate_limit_uploads: int = 10
    rate_limit_login_attempts: int = 10
    rate_limit_window_seconds: int = 60
    outbox_poll_seconds: int = 5
    task_lease_seconds: int = 300

    def required(self, field_name: str) -> str:
        value = getattr(self, field_name)
        if not value:
            env_name = f"CLOUDTASK_{field_name.upper()}"
            raise RuntimeError(f"{env_name} must be configured")
        return value

    def required_jwt_secret(self) -> str:
        secret = self.required("jwt_secret")
        if len(secret) < 32:
            raise RuntimeError("CLOUDTASK_JWT_SECRET must be at least 32 characters")
        return secret

    @cached_property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
