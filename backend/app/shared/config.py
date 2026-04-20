"""集中定义后端运行配置与派生路径。"""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


BACKEND_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    """封装环境变量和项目运行时默认配置。"""

    model_config = SettingsConfigDict(env_file=str(ENV_FILE), extra="ignore")

    PROJECT_NAME: str = "Agent Security Platform"

    FASTAPI_PORT: int = 8000
    FASTAPI_HOST: str = "127.0.0.1"

    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "postgres"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"

    SQLALCHEMY_ECHO: bool = Field(default=False)
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080
    PAUSE_TIMEOUT_MINUTES: int = 60
    SIMULATED_DATASET_STEP_SECONDS: float = 2.0
    RUN_CLAIM_STALE_AFTER_SECONDS: int = 30
    WORKER_POLL_INTERVAL_SECONDS: float = 1.0
    WORKER_RUNNER_HOST: str = "127.0.0.1"
    WORKER_MAX_ACTIVE_RUNS: int = 2
    WORKER_MAX_PARALLEL_EXECUTIONS_PER_RUN: int = 2
    WORKER_HEARTBEAT_INTERVAL_SECONDS: float = 5.0
    WORKER_RUNNER_START_TIMEOUT_SECONDS: float = 20.0
    WORKER_EXECUTION_TIMEOUT_SECONDS: int = 900
    WORKER_DISPATCH_MODE_DEFAULT: str = "synthetic_local"
    WORKER_NAMESPACE_ISOLATION_ENABLED: bool = True
    RUNTIME_ROOT_DIR: str | None = None

    @property
    def DATABASE_URL(self) -> URL:
        return URL.create(
            "postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            database=self.POSTGRES_DB,
        )

    @property
    def SYNC_DATABASE_URL(self) -> URL:
        return URL.create(
            "postgresql+psycopg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            database=self.POSTGRES_DB,
        )

    @property
    def runtime_root(self) -> Path:
        if self.RUNTIME_ROOT_DIR:
            return Path(self.RUNTIME_ROOT_DIR).expanduser().resolve()
        return BACKEND_DIR / "runtime"

    @property
    def uploads_root(self) -> Path:
        return self.runtime_root / "uploads"

    @property
    def avatars_root(self) -> Path:
        return self.uploads_root / "avatars"

    @property
    def credential_storage_dir(self) -> Path:
        return self.runtime_root / "credentials"

    @property
    def worker_workdir_root(self) -> Path:
        return self.runtime_root / "workdir"

    @property
    def CREDENTIAL_STORAGE_DIR(self) -> Path:
        return self.credential_storage_dir


settings = Settings()
