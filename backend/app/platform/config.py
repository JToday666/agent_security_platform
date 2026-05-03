"""集中定义后端运行配置与派生路径。"""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = BACKEND_DIR.parent
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
    WORKER_MAX_ACTIVE_RUNTIME_PROCESSES: int = 4
    RUNTIME_ROOT_DIR: str | None = None
    DATASET_ROOT_DIR: str | None = None
    DATASET_METADATA_ROOT_DIR: str | None = None
    AGENT_HTTP_ALLOW_PRIVATE_NETWORKS: bool = False
    AGENT_HTTP_MAX_REDIRECTS: int = 3
    AGENT_HTTP_RESPONSE_MAX_BYTES: int = 1_000_000
    LLM_JUDGE_PROVIDER: str = "deepseek"
    LLM_JUDGE_MODEL: str | None = None
    LLM_JUDGE_BASE_URL: str | None = None
    LLM_JUDGE_API_KEY: str | None = None
    LLM_JUDGE_TIMEOUT_SECONDS: float = 60.0
    LLM_JUDGE_MAX_TOKENS: int = 2000
    LLM_JUDGE_TEMPERATURE: float = 0.0
    LLM_JUDGE_MAX_EVENTS: int = 160

    @property
    def DATABASE_URL(self) -> URL:
        """返回业务运行时使用的异步数据库连接地址。"""
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
        """返回 Alembic 迁移等同步场景使用的数据库连接地址。"""
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
        """返回后端运行期文件的根目录。"""
        if self.RUNTIME_ROOT_DIR:
            return Path(self.RUNTIME_ROOT_DIR).expanduser().resolve()
        return REPO_ROOT / "var" / "backend"

    @property
    def dataset_root(self) -> Path:
        """返回平台使用的一等数据集根目录。"""
        if self.DATASET_ROOT_DIR:
            return Path(self.DATASET_ROOT_DIR).expanduser().resolve()
        return REPO_ROOT / "data" / "datasets"

    @property
    def dataset_metadata_root(self) -> Path:
        """返回数据集 registry/display_meta 的 JSON 真源目录。"""
        if self.DATASET_METADATA_ROOT_DIR:
            return Path(self.DATASET_METADATA_ROOT_DIR).expanduser().resolve()
        return REPO_ROOT / "data" / "metadata"

    @property
    def uploads_root(self) -> Path:
        """返回上传文件的统一存储目录。"""
        return self.runtime_root / "uploads"

    @property
    def avatars_root(self) -> Path:
        """返回用户头像文件的存储目录。"""
        return self.uploads_root / "avatars"

    @property
    def credential_storage_dir(self) -> Path:
        """返回凭据引用文件的落盘目录。"""
        return self.runtime_root / "credentials"

    @property
    def worker_workdir_root(self) -> Path:
        """返回 worker 运行样本时使用的工作目录根路径。"""
        return self.runtime_root / "workdir"


settings = Settings()
