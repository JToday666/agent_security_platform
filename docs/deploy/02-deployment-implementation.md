# 主环境部署实施手册

> 文件建议路径：`docs/deploy/02-deployment-implementation.md`  
> 适用对象：开发人员、运维人员、自动化 Agent  
> 适用环境：阿里云 A10 GPU ECS 主环境  
> 当前状态：PostgreSQL、vLLM、LiteLLM、Nginx Gateway 已验证运行；Backend API、scheduler、worker、migration 尚待接入

---

## 1. 基础前提

服务器已具备：

```text
Ubuntu 24.04.4 LTS
NVIDIA A10 GPU
NVIDIA Driver 580.126.09
Docker Engine 29.3.1
Docker Compose v5.1.1
Docker Root Dir = /data/docker
NVIDIA Container Runtime
/data 数据盘
ACR VPC 拉取能力
Xray 本机代理 127.0.0.1:10808
uv
```

不需要重复安装：

```text
NVIDIA Driver
CUDA Toolkit
Docker Engine
NVIDIA Container Toolkit
```

---

## 2. 初始化运行目录

```bash
mkdir -p \
  /data/agent-security-platform/compose \
  /data/agent-security-platform/env/prod \
  /data/agent-security-platform/services/postgresql/data \
  /data/agent-security-platform/services/postgresql/init \
  /data/agent-security-platform/models/text \
  /data/agent-security-platform/models/vision \
  /data/agent-security-platform/cache/modelscope \
  /data/agent-security-platform/cache/huggingface \
  /data/agent-security-platform/cache/vllm \
  /data/agent-security-platform/cache/uv \
  /data/agent-security-platform/cache/pip \
  /data/agent-security-platform/cache/pnpm \
  /data/agent-security-platform/cache/playwright \
  /data/agent-security-platform/logs/postgres \
  /data/agent-security-platform/logs/vllm \
  /data/agent-security-platform/logs/backend \
  /data/agent-security-platform/logs/worker \
  /data/agent-security-platform/backups/postgresql \
  /data/agent-security-platform/data/datasets \
  /data/agent-security-platform/data/uploads \
  /data/agent-security-platform/runtime \
  /data/agent-security-platform/artifacts \
  /data/agent-security-platform/tmp
```

---

## 3. 用户级缓存和代理

### 3.1 `~/.asp-cache-env`

```bash
export ASP_HOME="/data/agent-security-platform"

export MODELSCOPE_CACHE="$ASP_HOME/cache/modelscope"

export HF_HOME="$ASP_HOME/cache/huggingface"
export TRANSFORMERS_CACHE="$ASP_HOME/cache/huggingface"

export UV_CACHE_DIR="$ASP_HOME/cache/uv"
export PIP_CACHE_DIR="$ASP_HOME/cache/pip"
```

### 3.2 `~/.proxy-env`

```bash
export HTTP_PROXY="http://127.0.0.1:10808"
export HTTPS_PROXY="http://127.0.0.1:10808"
export http_proxy="$HTTP_PROXY"
export https_proxy="$HTTPS_PROXY"

export NO_PROXY="localhost,127.0.0.1,::1,172.16.0.0/12,10.0.0.0/8,192.168.0.0/16,100.100.100.200,crpi-5gm6gpgyiqxur1oj-vpc.cn-beijing.personal.cr.aliyuncs.com,modelscope.cn,.modelscope.cn,aliyuncs.com,.aliyuncs.com,aliyun.com,.aliyun.com,mirrors.aliyun.com,pypi.tuna.tsinghua.edu.cn,mirrors.tuna.tsinghua.edu.cn,registry.npmmirror.com,npmmirror.com,.npmmirror.com"
export no_proxy="$NO_PROXY"
```

### 3.3 `.bashrc` 末尾建议

```bash
if [ -f "$HOME/.local/bin/env" ]; then
  . "$HOME/.local/bin/env"
fi

if [ -f "$HOME/.asp-cache-env" ]; then
  . "$HOME/.asp-cache-env"
fi

if [ -f "$HOME/.proxy-env" ]; then
  . "$HOME/.proxy-env"
fi

proxy-on() {
  if [ -f "$HOME/.proxy-env" ]; then
    . "$HOME/.proxy-env"
    echo "proxy on: $HTTP_PROXY"
  else
    echo "missing $HOME/.proxy-env"
    return 1
  fi
}

proxy-off() {
  unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy NO_PROXY no_proxy
  echo "proxy off"
}

proxy-status() {
  echo "HTTP_PROXY=${HTTP_PROXY:-}"
  echo "HTTPS_PROXY=${HTTPS_PROXY:-}"
  echo "NO_PROXY=${NO_PROXY:-}"
}
```

---

## 4. PostgreSQL 部署

### 4.1 环境变量

`/data/agent-security-platform/env/prod/postgres.env`：

```env
POSTGRES_DB=postgres
POSTGRES_USER=asp_admin
POSTGRES_PASSWORD=<admin-password>

ASP_APP_DB=asp_db
ASP_APP_USER=asp_app
ASP_APP_PASSWORD=<app-password>

ASP_TEST_DB=test_db
ASP_TEST_USER=asp_test
ASP_TEST_PASSWORD=<test-password>
```

如果密码包含 `@`，写入 `DATABASE_URL` 时必须编码为 `%40`。

### 4.2 初始化脚本

`/data/agent-security-platform/services/postgresql/init/01-create-app-databases.sh`：

```bash
#!/usr/bin/env bash
set -euo pipefail

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<SQL
CREATE USER ${ASP_APP_USER} WITH PASSWORD '${ASP_APP_PASSWORD}';
CREATE USER ${ASP_TEST_USER} WITH PASSWORD '${ASP_TEST_PASSWORD}';

CREATE DATABASE ${ASP_APP_DB} OWNER ${ASP_APP_USER};
CREATE DATABASE ${ASP_TEST_DB} OWNER ${ASP_TEST_USER};

REVOKE ALL ON DATABASE ${ASP_APP_DB} FROM PUBLIC;
REVOKE ALL ON DATABASE ${ASP_TEST_DB} FROM PUBLIC;

GRANT CONNECT ON DATABASE ${ASP_APP_DB} TO ${ASP_APP_USER};
GRANT CONNECT ON DATABASE ${ASP_TEST_DB} TO ${ASP_TEST_USER};
SQL
```

```bash
chmod +x /data/agent-security-platform/services/postgresql/init/01-create-app-databases.sh
```

### 4.3 Compose

`/data/agent-security-platform/compose/docker-compose.postgres.yml`：

```yaml
services:
  postgres:
    image: crpi-5gm6gpgyiqxur1oj-vpc.cn-beijing.personal.cr.aliyuncs.com/agent_platform/asp_docker:postgres-17
    container_name: asp-postgres
    restart: unless-stopped

    env_file:
      - /data/agent-security-platform/env/prod/postgres.env

    ports:
      - "127.0.0.1:5432:5432"

    volumes:
      - /data/agent-security-platform/services/postgresql/data:/var/lib/postgresql/data
      - /data/agent-security-platform/services/postgresql/init:/docker-entrypoint-initdb.d:ro

    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U asp_admin -d postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 20s

    logging:
      driver: json-file
      options:
        max-size: "50m"
        max-file: "5"
```

### 4.4 启动与验证

```bash
cd /data/agent-security-platform/compose
docker compose -f docker-compose.postgres.yml up -d
docker compose -f docker-compose.postgres.yml ps
```

```bash
docker exec -it asp-postgres \
  psql -U asp_app -d asp_db \
  -c "SELECT current_user, current_database();"
```

```bash
docker exec -it asp-postgres \
  psql -U asp_test -d test_db \
  -c "SELECT current_user, current_database();"
```

---

## 5. vLLM 部署

### 5.1 模型下载

模型：

```text
Qwen/Qwen2.5-14B-Instruct-GPTQ-Int4
```

下载路径：

```text
/data/agent-security-platform/models/text/Qwen2.5-14B-Instruct-GPTQ-Int4
```

用 uv 创建 ModelScope 环境：

```bash
mkdir -p /data/agent-security-platform/tools/modelscope
cd /data/agent-security-platform/tools/modelscope

uv venv --python 3.12 .venv
source .venv/bin/activate
uv pip install -U modelscope
```

ModelScope 建议直连：

```bash
proxy-off
export MODELSCOPE_CACHE=/data/agent-security-platform/cache/modelscope
```

下载：

```bash
modelscope download \
  --model Qwen/Qwen2.5-14B-Instruct-GPTQ-Int4 \
  --local_dir /data/agent-security-platform/models/text/Qwen2.5-14B-Instruct-GPTQ-Int4
```

验证模型：

```bash
MODEL_DIR="/data/agent-security-platform/models/text/Qwen2.5-14B-Instruct-GPTQ-Int4"

ls -lh "$MODEL_DIR"
du -sh "$MODEL_DIR"
test -f "$MODEL_DIR/config.json" && echo "config.json ok"
test -f "$MODEL_DIR/tokenizer.json" && echo "tokenizer.json ok"
find "$MODEL_DIR" -maxdepth 1 -type f | sort
```

下载完成后恢复默认代理：

```bash
proxy-on
```

### 5.2 Compose

`/data/agent-security-platform/compose/docker-compose.vllm.yml`：

```yaml
services:
  vllm:
    image: crpi-5gm6gpgyiqxur1oj-vpc.cn-beijing.personal.cr.aliyuncs.com/agent_platform/asp_docker:vllm-openai-latest
    container_name: asp-vllm
    restart: unless-stopped

    gpus: all
    ipc: host

    environment:
      NVIDIA_VISIBLE_DEVICES: all
      NVIDIA_DRIVER_CAPABILITIES: compute,utility
      HF_HOME: /root/.cache/huggingface
      TRANSFORMERS_CACHE: /root/.cache/huggingface

    ports:
      - "127.0.0.1:18000:8000"

    volumes:
      - /data/agent-security-platform/models:/models:ro
      - /data/agent-security-platform/cache/huggingface:/root/.cache/huggingface
      - /data/agent-security-platform/cache/vllm:/root/.cache/vllm
      - /data/agent-security-platform/logs/vllm:/logs

    entrypoint:
      - vllm
      - serve

    command:
      - /models/text/Qwen2.5-14B-Instruct-GPTQ-Int4
      - --host
      - 0.0.0.0
      - --port
      - "8000"
      - --served-model-name
      - qwen2.5-14b-gptq-int4
      - --trust-remote-code
      - --quantization
      - gptq
      - --gpu-memory-utilization
      - "0.85"
      - --max-model-len
      - "8192"

    logging:
      driver: json-file
      options:
        max-size: "100m"
        max-file: "5"
```

注意：不要使用 `/bin/bash -lc` 加数组形式 command，这会导致 `serve` 被当成 shell 位置参数，vLLM 只打印顶层 usage 而不启动服务。

### 5.3 启动与验证

```bash
cd /data/agent-security-platform/compose
docker compose -f docker-compose.vllm.yml up -d
docker compose -f docker-compose.vllm.yml ps
docker logs -f asp-vllm
```

看到以下信息表示启动完成：

```text
Starting vLLM server on http://0.0.0.0:8000
Application startup complete
```

验证底层 vLLM 模型列表：

```bash
curl -s http://127.0.0.1:18000/v1/models | python3 -m json.tool
```

验证底层 vLLM 聊天接口：

```bash
curl http://127.0.0.1:18000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5-14b-gptq-int4",
    "messages": [
      {"role": "user", "content": "用一句话介绍智能体安全评测平台。"}
    ],
    "max_tokens": 128,
    "temperature": 0.2,
    "top_p": 0.8,
    "repetition_penalty": 1.05
  }'
```

生产后端默认不直接连接该宿主机端口，而是通过 `asp-litellm` 访问模型代理。
如果当前服务器没有发布 `127.0.0.1:18000`，以 LiteLLM 的 `127.0.0.1:18400`
调试入口为准。

---

## 6. Backend 环境变量

`/data/agent-security-platform/env/prod/backend.env` 用于后端容器时必须使用容器网络地址。真实密钥只写入
主机 `/data/agent-security-platform/env/prod/backend.env`，不要提交到 Git；仓库内模板见
`docs/deploy/templates/backend/backend.env.example`。

不要把宿主机本地联调用的 `127.0.0.1` 地址直接用于 Docker 后端容器。后端容器访问数据库和 LLM 时应使用 `asp-postgres`、`asp-litellm` 这类 Docker DNS 名称。

```env
APP_ENV=production
PROJECT_NAME=agent-security-platform
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000
LOG_LEVEL=INFO
TZ=Asia/Shanghai
PUBLIC_BASE_URL=https://<domain>

DATABASE_URL=postgresql+psycopg://asp_app:<password>@asp-postgres:5432/asp_db
SECRET_KEY=<replace-with-strong-secret>

ASP_DATA_ROOT=/data/agent-security-platform
DATASET_ROOT_DIR=/data/agent-security-platform/data/datasets
DATASET_METADATA_ROOT_DIR=/data/agent-security-platform/data/dataset-registry
UPLOAD_ROOT_DIR=/data/agent-security-platform/data/uploads
RUNTIME_ROOT_DIR=/data/agent-security-platform/runtime
TMP_ROOT_DIR=/data/agent-security-platform/tmp
LOG_ROOT_DIR=/data/agent-security-platform/logs

WORKER_RUNTIME_LAUNCH_MODE=docker
WORKER_RUNTIME_DOCKER_IMAGE=<provided-by-compose-BACKEND_IMAGE>
WORKER_RUNTIME_DOCKER_NETWORK=asp-runtime-net
WORKER_RUNTIME_DOCKER_PORT=8000
WORKER_RUNTIME_DOCKER_CONTAINER_WORKDIR=/runtime
WORKER_RUNTIME_DOCKER_CPUS=1.0
WORKER_RUNTIME_DOCKER_MEMORY=1g
WORKER_RUNTIME_DOCKER_STOP_TIMEOUT_SECONDS=10.0
RUNTIME_SESSION_TTL_SECONDS=900
RUNTIME_GATEWAY_COOKIE_NAME=asp_runtime_token
RUNTIME_REAPER_INTERVAL_SECONDS=30
RUNTIME_CONTAINER_REAPER_ENABLED=true

SCHEDULER_POLL_INTERVAL_SECONDS=1.0
SCHEDULER_RELEASE_BATCH_SIZE=20
GLOBAL_MAX_IN_FLIGHT_SAMPLES=16
RUN_MAX_IN_FLIGHT_SAMPLES=4
USER_MAX_IN_FLIGHT_SAMPLES=8
AGENT_MAX_IN_FLIGHT_SAMPLES=4
SAMPLE_WORKER_MAX_ACTIVE_EXECUTIONS=1
SAMPLE_CLAIM_STALE_AFTER_SECONDS=90
SAMPLE_HEARTBEAT_INTERVAL_SECONDS=10.0
SAMPLE_MAX_ATTEMPTS=2

LLM_JUDGE_PROVIDER=litellm
LLM_BASE_URL=http://asp-litellm:4000/v1
LLM_DEFAULT_MODEL=local-qwen
LLM_API_KEY=<litellm-master-key>

CORS_ALLOWED_ORIGINS=https://<domain>
```

宿主机临时运行 Backend 时使用：

```env
DATABASE_URL=postgresql+psycopg://asp_app:<password>@127.0.0.1:5432/asp_db
LLM_BASE_URL=http://127.0.0.1:18400/v1
LLM_DEFAULT_MODEL=local-qwen
LLM_API_KEY=<litellm-master-key>
```

如果服务器上已有 `/data/agent-security-platform/env/prod/backend.env` 但其中仍是 `127.0.0.1`，说明它只能直接用于宿主机临时运行。
Docker 后端启动前，最终生效的 `DATABASE_URL` 和 `LLM_BASE_URL` 必须来自上面的容器网络地址；
可以直接修改 `backend.env`，也可以通过 compose `.env` 中的 `BACKEND_DATABASE_URL` 和
`BACKEND_LLM_BASE_URL` 覆盖。

---

## 7. Backend Compose 模板

后端容器统一使用同一个不可变镜像 tag。API、scheduler、sample worker、
Alembic migration 和 worker 后续启动的一次性 runtime runner 都使用该镜像。
Compose 模板在仓库中维护：

```text
backend/Dockerfile
docs/deploy/templates/backend/docker-compose.backend.yml
docs/deploy/templates/backend/backend.env.example
```

部署到主环境时建议放到：

```text
/data/agent-security-platform/services/backend/compose/docker-compose.yml
/data/agent-security-platform/services/backend/compose/.env
```

`.env` 保存本次发布使用的不可变镜像和容器网络连接地址；模板见
`docs/deploy/templates/backend/compose.env.example`：

```env
BACKEND_IMAGE=crpi-5gm6gpgyiqxur1oj-vpc.cn-beijing.personal.cr.aliyuncs.com/agent_platform/asp_code:backend-<git-sha>
BACKEND_DATABASE_URL=postgresql+psycopg://asp_app:<password>@asp-postgres:5432/asp_db
BACKEND_LLM_BASE_URL=http://asp-litellm:4000/v1
```

首次部署前确保外部网络存在，并把 PostgreSQL 加入 DB 网络：

```bash
docker network create asp-net || true
docker network create asp-db-net || true
docker network create asp-ai-net || true
docker network create asp-runtime-net || true
docker network connect asp-db-net asp-postgres || true
```

检查网络连接：

```bash
docker network inspect asp-db-net --format '{{range .Containers}}{{.Name}} {{end}}'
docker network inspect asp-ai-net --format '{{range .Containers}}{{.Name}} {{end}}'
docker network inspect asp-net --format '{{range .Containers}}{{.Name}} {{end}}'
```

期望至少看到：

```text
asp-db-net: asp-postgres
asp-ai-net: asp-litellm asp-vllm
asp-net: asp-nginx，后端启动后还有 backend-api
```

校验 Compose：

```bash
cd /data/agent-security-platform/services/backend/compose
docker compose config
```

迁移与启动：

```bash
docker compose pull
docker compose run --rm backend-migrate
docker compose up -d backend-api backend-scheduler backend-worker
docker compose ps
```

本地构建镜像调试时可用：

```bash
cd /home/ecs-user/apps/agent_security_platform
docker build \
  --build-arg BASE_IMAGE=crpi-5gm6gpgyiqxur1oj-vpc.cn-beijing.personal.cr.aliyuncs.com/agent_platform/asp_docker:python-3.12-slim \
  --build-arg DOCKER_CLI_IMAGE=crpi-5gm6gpgyiqxur1oj-vpc.cn-beijing.personal.cr.aliyuncs.com/agent_platform/asp_docker:docker-29-cli \
  -t asp-backend:local \
  backend
```

该 Dockerfile 默认使用清华 PyPI 源安装 Python 依赖，并在构建阶段把 Debian 源替换为阿里云镜像源。
`BASE_IMAGE` 和 `DOCKER_CLI_IMAGE` 在 ECS 上必须传入 ACR 镜像，避免构建时访问 Docker Hub。

然后把 `/data/agent-security-platform/services/backend/compose/.env` 中的 `BACKEND_IMAGE` 设为 `asp-backend:local`。

迁移前后可检查 Alembic 版本：

```bash
docker exec asp-postgres \
  psql -U asp_app -d asp_db \
  -c "SELECT version_num FROM alembic_version;"
```

关键边界：

- `backend-api`：只服务 FastAPI，经 `asp-net` 接收 Nginx 转发，不挂载 Docker socket。
- `backend-scheduler`：只做 run/sample 调度、过期 lease 恢复与 finalizer，不挂载 Docker socket。
- `backend-worker`：唯一挂载 `/var/run/docker.sock`，唯一负责按 sample 启动一次性 runtime runner。
- `backend-migrate`：一次性 Alembic job，执行成功后退出。
- runtime runner 使用 `backend-worker` 传入的 `WORKER_RUNTIME_DOCKER_IMAGE`，与上述 backend 服务保持同一镜像 tag。
- runtime runner 只加入 `asp-runtime-net`，使用容器内固定端口 `8000`，不发布宿主机动态端口。

```yaml
# 完整模板见 docs/deploy/templates/backend/docker-compose.backend.yml
```

`/healthz` 用于进程存活探针，`/readyz` 会检查数据库可达性。管理员可通过
`GET /api/v1/ops/workers` 查看 scheduler/sample worker 心跳、sample 队列计数和轻量告警。

---

## 8. Frontend 发布

```bash
VERSION="$(date +%Y%m%d_%H%M%S)_$(git rev-parse --short HEAD)"

mkdir -p "/data/agent-security-platform/www/frontend/releases/$VERSION"
rsync -a --delete frontend/dist/ "/data/agent-security-platform/www/frontend/releases/$VERSION/"

ln -sfn "/data/agent-security-platform/www/frontend/releases/$VERSION" \
  /data/agent-security-platform/www/frontend/current
```

Gateway root 指向：

```text
/data/agent-security-platform/www/frontend/current
```

---

## 9. Gateway 模板

### 9.1 Nginx location

当前服务器 Gateway 使用 `asp-nginx`。`/runtime/tasks/` 必须保留原始路径转发给
FastAPI，不能 strip prefix，也不能直接 proxy 到 runtime runner：

```nginx
location /api/ {
    proxy_pass http://backend-api:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

location /runtime/tasks/ {
    proxy_pass http://backend-api:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

### 9.2 Gateway Compose 模板

```yaml
services:
  gateway:
    image: nginx:1.27-alpine
    container_name: asp-nginx
    restart: unless-stopped
    ports:
      - "80:80"
    volumes:
      - /data/agent-security-platform/www/frontend/current:/usr/share/nginx/html:ro
      - /data/agent-security-platform/services/nginx/conf.d:/etc/nginx/conf.d:ro
    networks:
      - asp-net

networks:
  asp-net:
    external: true
```

如继续使用 ACR 中的自有 Nginx 镜像，只替换 `image`，容器名、网络和 upstream
仍按 `asp-nginx`、`asp-net`、`backend-api:8000` 对齐。

### 9.3 可选 Caddyfile

```caddy
:80 {
    root * /www/frontend/current
    encode zstd gzip

    handle /api/* {
        reverse_proxy backend-api:8000
    }

    handle /runtime/tasks/* {
        reverse_proxy backend-api:8000
    }

    handle {
        try_files {path} /index.html
        file_server
    }
}
```

### 9.4 可选 Caddy Compose 模板

```yaml
services:
  gateway:
    image: crpi-5gm6gpgyiqxur1oj-vpc.cn-beijing.personal.cr.aliyuncs.com/agent_platform/asp_docker:caddy-latest
    container_name: asp-caddy
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /data/agent-security-platform/www/frontend:/www/frontend:ro
      - /data/agent-security-platform/services/caddy/config/Caddyfile:/etc/caddy/Caddyfile:ro
      - /data/agent-security-platform/services/caddy/data:/data
      - /data/agent-security-platform/services/caddy/config:/config
```

---

## 10. 备份脚本

`/data/agent-security-platform/services/postgresql/backup.sh`：

```bash
#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="/data/agent-security-platform/backups/postgresql"
CONTAINER="asp-postgres"
DB="asp_db"
USER="asp_admin"
STAMP="$(date +%F-%H%M%S)"

mkdir -p "$BACKUP_DIR"

docker exec "$CONTAINER" pg_dump -U "$USER" "$DB" \
  | gzip > "$BACKUP_DIR/${DB}-${STAMP}.sql.gz"

gzip -t "$BACKUP_DIR/${DB}-${STAMP}.sql.gz"

find "$BACKUP_DIR" -type f -name "*.sql.gz" -mtime +14 -delete

echo "backup created: $BACKUP_DIR/${DB}-${STAMP}.sql.gz"
```

```bash
chmod +x /data/agent-security-platform/services/postgresql/backup.sh
/data/agent-security-platform/services/postgresql/backup.sh
```

Crontab：

```cron
30 3 * * * /data/agent-security-platform/services/postgresql/backup.sh >> /data/agent-security-platform/logs/postgres/backup.log 2>&1
```
