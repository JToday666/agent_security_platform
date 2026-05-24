# 主环境部署实施手册

> 文件建议路径：`docs/deploy/02-deployment-implementation.md`  
> 适用对象：开发人员、运维人员、自动化 Agent  
> 适用环境：阿里云 A10 GPU ECS 主环境  
> 当前状态：PostgreSQL 与 vLLM 已验证通过；Backend、Worker、Frontend、Gateway 待接入

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

验证模型列表：

```bash
curl -s http://127.0.0.1:18000/v1/models | python3 -m json.tool
```

验证聊天接口：

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

---

## 6. Backend 环境变量

`/data/agent-security-platform/env/prod/backend.env`：

```env
APP_ENV=production
PROJECT_NAME=agent-security-platform
TZ=Asia/Shanghai

DATABASE_URL=postgresql+psycopg://asp_app:<password>@127.0.0.1:5432/asp_db

ASP_DATA_ROOT=/data/agent-security-platform
DATASET_ROOT_DIR=/data/agent-security-platform/data/datasets
DATASET_METADATA_ROOT_DIR=/data/agent-security-platform/data/dataset-registry
UPLOAD_ROOT_DIR=/data/agent-security-platform/data/uploads
RUNTIME_ROOT_DIR=/data/agent-security-platform/runtime
TMP_ROOT_DIR=/data/agent-security-platform/tmp
LOG_ROOT_DIR=/data/agent-security-platform/logs

WORKER_RUNNER_HOST=172.17.0.1
WORKER_BROWSER_ENTRY_HOST=host.docker.internal
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
LLM_BASE_URL=http://127.0.0.1:18000/v1
LLM_DEFAULT_MODEL=qwen2.5-14b-gptq-int4

PUBLIC_BASE_URL=https://<domain>
CORS_ALLOWED_ORIGINS=https://<domain>
```

宿主机临时运行 Backend 时使用：

```env
DATABASE_URL=postgresql+psycopg://asp_app:<password>@127.0.0.1:5432/asp_db
LLM_BASE_URL=http://127.0.0.1:18000/v1
LLM_DEFAULT_MODEL=qwen2.5-14b-gptq-int4
```

---

## 7. Backend / Worker Compose 模板

实际镜像名称按项目 Dockerfile 调整。

```yaml
services:
  backend:
    image: crpi-5gm6gpgyiqxur1oj-vpc.cn-beijing.personal.cr.aliyuncs.com/agent_platform/asp_code:backend-latest
    container_name: asp-backend
    restart: unless-stopped
    env_file:
      - /data/agent-security-platform/env/prod/backend.env
    ports:
      - "127.0.0.1:8000:8000"
    volumes:
      - /data/agent-security-platform/data:/app/data
      - /data/agent-security-platform/runtime:/app/runtime
      - /data/agent-security-platform/artifacts:/app/artifacts
      - /data/agent-security-platform/logs/backend:/app/logs
    command: ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

  scheduler:
    image: crpi-5gm6gpgyiqxur1oj-vpc.cn-beijing.personal.cr.aliyuncs.com/agent_platform/asp_code:backend-latest
    container_name: asp-scheduler
    restart: unless-stopped
    env_file:
      - /data/agent-security-platform/env/prod/backend.env
    volumes:
      - /data/agent-security-platform/data:/app/data
      - /data/agent-security-platform/runtime:/app/runtime
      - /data/agent-security-platform/artifacts:/app/artifacts
      - /data/agent-security-platform/logs/scheduler:/app/logs
    command: ["python", "scheduler.py"]

  worker:
    image: crpi-5gm6gpgyiqxur1oj-vpc.cn-beijing.personal.cr.aliyuncs.com/agent_platform/asp_code:backend-latest
    restart: unless-stopped
    deploy:
      replicas: 2
    env_file:
      - /data/agent-security-platform/env/prod/backend.env
    volumes:
      - /data/agent-security-platform/data:/app/data
      - /data/agent-security-platform/runtime:/app/runtime
      - /data/agent-security-platform/artifacts:/app/artifacts
      - /data/agent-security-platform/logs/worker:/app/logs
      # 仅当 Worker 需要创建 runtime-runner 容器时启用
      # - /var/run/docker.sock:/var/run/docker.sock
    command: ["python", "worker.py"]
```

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

### 9.1 Caddyfile

```caddy
:80 {
    root * /www/frontend/current
    encode zstd gzip

    handle_path /api/* {
        reverse_proxy backend:8000
    }

    handle {
        try_files {path} /index.html
        file_server
    }
}
```

### 9.2 Gateway Compose 模板

```yaml
services:
  gateway:
    image: crpi-5gm6gpgyiqxur1oj-vpc.cn-beijing.personal.cr.aliyuncs.com/agent_platform/asp_docker:caddy-latest
    container_name: asp-gateway
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
