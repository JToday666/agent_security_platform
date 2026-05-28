"""集中定义后端运行配置与派生路径。"""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL, make_url

BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = BACKEND_DIR.parent
ENV_FILE = BACKEND_DIR / ".env"
DEFAULT_DATA_ROOT = Path("/data/agent-security-platform")


class Settings(BaseSettings):
    """封装环境变量和项目运行时默认配置。"""

    model_config = SettingsConfigDict(env_file=str(ENV_FILE), extra="ignore")

    PROJECT_NAME: str = "Agent Security Platform"

    FASTAPI_PORT: int = 8000
    FASTAPI_HOST: str = "127.0.0.1"
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_ENV: str = "dev"
    LOG_SERVICE_NAME: str = "backend"
    PUBLIC_BASE_URL: str = "http://127.0.0.1:8000"

    DATABASE_URL_RAW: str | None = Field(default=None, validation_alias="DATABASE_URL")
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
    WORKER_POLL_INTERVAL_SECONDS: float = 1.0
    WORKER_RUNNER_HOST: str = "127.0.0.1"
    WORKER_BROWSER_ENTRY_HOST: str | None = None
    SCHEDULER_POLL_INTERVAL_SECONDS: float = 1.0
    SCHEDULER_RELEASE_BATCH_SIZE: int = 20
    GLOBAL_MAX_IN_FLIGHT_SAMPLES: int = 16
    RUN_MAX_IN_FLIGHT_SAMPLES: int = 4
    USER_MAX_IN_FLIGHT_SAMPLES: int = 8
    AGENT_MAX_IN_FLIGHT_SAMPLES: int = 4
    SAMPLE_WORKER_MAX_ACTIVE_EXECUTIONS: int = 1
    SAMPLE_CLAIM_STALE_AFTER_SECONDS: int = 90
    SAMPLE_HEARTBEAT_INTERVAL_SECONDS: float = 10.0
    SAMPLE_MAX_ATTEMPTS: int = 2
    WORKER_RUNTIME_LAUNCH_MODE: str = "process"
    WORKER_RUNTIME_DOCKER_IMAGE: str = "agent-security-platform-runtime:latest"
    WORKER_RUNTIME_DOCKER_NETWORK: str = "asp-runtime-net"
    WORKER_RUNTIME_DOCKER_PORT: int = 8000
    WORKER_RUNTIME_DOCKER_CONTAINER_WORKDIR: str = "/runtime"
    WORKER_RUNTIME_DOCKER_CPUS: str = "1.0"
    WORKER_RUNTIME_DOCKER_MEMORY: str = "1g"
    WORKER_RUNTIME_DOCKER_STOP_TIMEOUT_SECONDS: float = 10.0
    WORKER_RUNNER_START_TIMEOUT_SECONDS: float = 20.0
    WORKER_EXECUTION_TIMEOUT_SECONDS: int = 900
    WORKER_DISPATCH_MODE_DEFAULT: str = "synthetic_local"
    WORKER_NAMESPACE_ISOLATION_ENABLED: bool = True
    WORKER_MAX_ACTIVE_RUNTIME_PROCESSES: int = 4
    RUNTIME_SESSION_TTL_SECONDS: int = 900
    RUNTIME_GATEWAY_COOKIE_NAME: str = "asp_runtime_token"
    RUNTIME_REAPER_INTERVAL_SECONDS: float = 30.0
    RUNTIME_CONTAINER_REAPER_ENABLED: bool = True
    ASP_DATA_ROOT: str | None = None
    RUNTIME_ROOT_DIR: str | None = None
    DATASET_ROOT_DIR: str | None = None
    DATASET_METADATA_ROOT_DIR: str | None = None
    UPLOAD_ROOT_DIR: str | None = None
    TMP_ROOT_DIR: str | None = None
    LOG_ROOT_DIR: str | None = None
    ARTIFACT_ROOT_DIR: str | None = None
    AGENT_HTTP_ALLOW_PRIVATE_NETWORKS: bool = False
    AGENT_HTTP_MAX_REDIRECTS: int = 3
    AGENT_HTTP_RESPONSE_MAX_BYTES: int = 1_000_000
    AGENT_HTTP_EVIDENCE_MAX_BODY_CHARS: int = 4_000
    LLM_BASE_URL: str | None = None
    LLM_DEFAULT_MODEL: str | None = None
    LLM_API_KEY: str | None = None
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
        if self.DATABASE_URL_RAW:
            return self._database_url_with_driver("postgresql+asyncpg")
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
        if self.DATABASE_URL_RAW:
            return self._database_url_with_driver("postgresql+psycopg")
        return URL.create(
            "postgresql+psycopg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            database=self.POSTGRES_DB,
        )

    def _database_url_with_driver(self, drivername: str) -> URL:
        """按调用场景替换显式数据库 URL 的 SQLAlchemy driver。"""
        assert self.DATABASE_URL_RAW is not None
        return make_url(self.DATABASE_URL_RAW).set(drivername=drivername)

    @staticmethod
    def _resolve_path(value: str | None, fallback: Path) -> Path:
        """Resolve an override path or return the provided fallback path."""
        if value:
            return Path(value).expanduser().resolve()
        return fallback.resolve()

    @staticmethod
    def _reject_project_storage_path(path: Path, env_name: str) -> Path:
        """Reject generated storage paths that would write inside this checkout."""
        resolved_path = path.resolve()
        repo_root = REPO_ROOT.resolve()
        if repo_root == Path("/"):
            repo_root = BACKEND_DIR.resolve()
        try:
            resolved_path.relative_to(repo_root)
        except ValueError:
            return resolved_path
        raise ValueError(
            f"{env_name} must not resolve inside project directory: {resolved_path}. "
            "Use /data/agent-security-platform for persistent runtime data, "
            "or a /tmp path for tests."
        )

    def _resolve_storage_path(
        self, value: str | None, fallback: Path, env_name: str
    ) -> Path:
        """Resolve and validate a server-generated storage path."""
        return self._reject_project_storage_path(
            self._resolve_path(value, fallback), env_name
        )

    @property
    def data_root(self) -> Path:
        """返回服务器数据根目录。"""
        return self._resolve_storage_path(
            self.ASP_DATA_ROOT, DEFAULT_DATA_ROOT, "ASP_DATA_ROOT"
        )

    @property
    def runtime_root(self) -> Path:
        """返回后端运行期文件的根目录。"""
        return self._resolve_storage_path(
            self.RUNTIME_ROOT_DIR, self.data_root / "runtime", "RUNTIME_ROOT_DIR"
        )

    @property
    def dataset_root(self) -> Path:
        """返回平台使用的一等数据集根目录。"""
        return self._resolve_storage_path(
            self.DATASET_ROOT_DIR,
            self.data_root / "data" / "datasets",
            "DATASET_ROOT_DIR",
        )

    @property
    def dataset_metadata_root(self) -> Path:
        """返回数据集 registry/display_meta 的 JSON 真源目录。"""
        return self._resolve_storage_path(
            self.DATASET_METADATA_ROOT_DIR,
            self.data_root / "data" / "dataset-registry",
            "DATASET_METADATA_ROOT_DIR",
        )

    @property
    def uploads_root(self) -> Path:
        """返回上传文件的统一存储目录。"""
        return self._resolve_storage_path(
            self.UPLOAD_ROOT_DIR,
            self.data_root / "data" / "uploads",
            "UPLOAD_ROOT_DIR",
        )

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

    @property
    def tmp_root(self) -> Path:
        """返回后端临时文件根目录。"""
        return self._resolve_storage_path(
            self.TMP_ROOT_DIR, self.data_root / "tmp", "TMP_ROOT_DIR"
        )

    @property
    def log_root(self) -> Path:
        """返回后端日志根目录。"""
        return self._resolve_storage_path(
            self.LOG_ROOT_DIR, self.data_root / "logs", "LOG_ROOT_DIR"
        )

    @property
    def artifact_root(self) -> Path:
        """返回评测产物归档根目录。"""
        return self._resolve_storage_path(
            self.ARTIFACT_ROOT_DIR,
            self.data_root / "artifacts",
            "ARTIFACT_ROOT_DIR",
        )


settings = Settings()
