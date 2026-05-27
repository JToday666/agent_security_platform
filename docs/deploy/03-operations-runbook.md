# 运维与 Agent 操作手册

> 文件建议路径：`docs/deploy/03-operations-runbook.md`  
> 适用对象：开发人员、运维人员、自动化 Agent  
> 目标：提供可执行的检查、启停、排错、备份、发布和安全操作规范

---

## 1. 快速状态检查

```bash
docker ps
nvidia-smi
df -hT / /data
docker info | grep "Docker Root Dir"
docker network ls
```

期望：

```text
Docker Root Dir: /data/docker
asp-postgres Up healthy
asp-vllm Up
asp-litellm Up
asp-nginx Up healthy
nvidia-smi 显示 VLLM::EngineCore 占用显存
/data 有足够剩余空间
```

后端部署前还需要确认：

```bash
test -f /data/agent-security-platform/services/backend/compose/docker-compose.yml
test -f /data/agent-security-platform/services/backend/compose/.env
test -f /data/agent-security-platform/env/prod/backend.env
docker network inspect asp-db-net --format '{{range .Containers}}{{.Name}} {{end}}'
docker images --format '{{.Repository}}:{{.Tag}}' | grep -E 'asp_code:backend|asp-backend'
```

期望：

```text
compose 文件存在。
asp-db-net 中有 asp-postgres。
存在本次发布要用的后端镜像。
Docker 后端最终生效的 DATABASE_URL 使用 asp-postgres，不使用 127.0.0.1。
worker 的 LLM_BASE_URL 来自 backend-worker.env，使用 asp-litellm，不由 API 或 scheduler 继承。
```

### 1.1 Runtime Gateway 验证

```bash
curl -fsS http://127.0.0.1/healthz
curl -fsS http://127.0.0.1/readyz
curl -fsS http://127.0.0.1/api/v1/
curl -fsS -H "Authorization: Bearer <admin-token>" \
  http://127.0.0.1/api/v1/ops/workers
docker ps --filter label=managedBy=asp-worker \
  --format '{{.Names}} {{.Ports}} {{.Label "sampleExecutionId"}}'
```

期望：

```text
/healthz、/readyz 只在它们被网关代理到后端时才证明后端状态；当前 Nginx 可用前端 SPA 时，非 /api 路径也可能返回 200。
/api/v1/ 返回后端 envelope。若返回 502，通常是 backend-api 尚未部署或未加入 asp-net。
/api/v1/ops/workers 返回 scheduler/sample_worker 心跳和 sampleQueues。
runtime runner 没有 0.0.0.0:随机端口或公网端口映射。
外部 Agent runtime URL 形如 /runtime/tasks/{sampleExecutionId}/...?token=...
过期 token、已关闭 session、非法 sampleExecutionId 不能访问 runtime 页面。
```

---

## 2. PostgreSQL 检查

### 2.1 容器状态

```bash
docker ps | grep asp-postgres
docker logs --tail 100 asp-postgres
```

### 2.2 数据库连接

生产库：

```bash
docker exec -it asp-postgres \
  psql -U asp_app -d asp_db \
  -c "SELECT current_user, current_database();"
```

测试库：

```bash
docker exec -it asp-postgres \
  psql -U asp_test -d test_db \
  -c "SELECT current_user, current_database();"
```

管理用户：

```bash
docker exec -it asp-postgres \
  psql -U asp_admin -d postgres \
  -c "\l"
```

---

## 3. LLM 服务检查

### 3.1 容器状态

```bash
docker ps | grep asp-vllm
docker ps | grep asp-litellm
docker logs --tail 200 asp-vllm
docker logs --tail 200 asp-litellm
nvidia-smi
```

### 3.2 LiteLLM 模型列表

```bash
set -a
. /data/agent-security-platform/env/prod/backend.env
set +a

curl -s http://127.0.0.1:18400/v1/models \
  -H "Authorization: Bearer ${LLM_API_KEY}" \
  | python3 -m json.tool
```

期望至少包含：

```text
local-qwen
```

未带 API key 访问 `http://127.0.0.1:18400/v1/models` 返回 `401` 是正常鉴权行为。

### 3.3 聊天测试

```bash
curl http://127.0.0.1:18400/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${LLM_API_KEY}" \
  -d '{
    "model": "local-qwen",
    "messages": [
      {"role": "user", "content": "用一句话介绍智能体安全评测平台。"}
    ],
    "max_tokens": 128,
    "temperature": 0.2
  }'
```

backend-worker 容器内应使用 `LLM_BASE_URL=http://asp-litellm:4000/v1`；
backend-api、backend-scheduler 和 backend-migrate 不应注入 LLM 配置。

---

## 4. 服务启停

### 4.1 PostgreSQL

```bash
cd /data/agent-security-platform/compose

docker compose -f docker-compose.postgres.yml up -d
docker compose -f docker-compose.postgres.yml restart
docker compose -f docker-compose.postgres.yml ps
```

停止：

```bash
docker compose -f docker-compose.postgres.yml stop
```

不要在数据库运行时删除：

```text
/data/agent-security-platform/services/postgresql/data
```

### 4.2 vLLM

```bash
cd /data/agent-security-platform/compose

docker compose -f docker-compose.vllm.yml up -d
docker compose -f docker-compose.vllm.yml restart
docker compose -f docker-compose.vllm.yml ps
docker logs -f asp-vllm
```

停止：

```bash
docker compose -f docker-compose.vllm.yml stop
```

### 4.3 Backend

```bash
cd /data/agent-security-platform/services/backend/compose

docker compose config
docker compose run --rm backend-migrate
docker compose up -d backend-api backend-scheduler backend-worker
docker compose ps
```

停止：

```bash
docker compose stop backend-api backend-scheduler backend-worker
```

查看日志：

```bash
docker compose logs -f backend-api
docker compose logs -f backend-scheduler
docker compose logs -f backend-worker
```

---

## 5. 数据库备份与恢复

### 5.1 手动备份

```bash
/data/agent-security-platform/services/postgresql/backup.sh
ls -lh /data/agent-security-platform/backups/postgresql
```

### 5.2 定时备份

```bash
crontab -l
```

建议存在：

```cron
30 3 * * * /data/agent-security-platform/services/postgresql/backup.sh >> /data/agent-security-platform/logs/postgres/backup.log 2>&1
```

### 5.3 恢复备份

恢复前必须确认目标库允许被覆盖，并提前备份当前状态。

```bash
gunzip -c /data/agent-security-platform/backups/postgresql/asp_db-YYYY-MM-DD-HHMMSS.sql.gz \
  | docker exec -i asp-postgres psql -U asp_admin -d asp_db
```

---

## 6. vLLM 常见故障

### 6.1 容器一直重启但日志只显示 vLLM usage

原因通常是 Compose 命令写法错误，例如使用 `/bin/bash -lc` 加数组形式 command，导致 `serve` 变成位置参数。

正确写法：

```yaml
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
```

### 6.2 GPU 显存不足

检查：

```bash
nvidia-smi
docker logs --tail 200 asp-vllm
```

处理：

```text
--max-model-len 8192 → 4096
--gpu-memory-utilization 0.85 → 0.80
```

重启：

```bash
cd /data/agent-security-platform/compose
docker compose -f docker-compose.vllm.yml restart
```

### 6.3 模型路径错误

宿主机路径：

```text
/data/agent-security-platform/models/text/Qwen2.5-14B-Instruct-GPTQ-Int4
```

容器内路径：

```text
/models/text/Qwen2.5-14B-Instruct-GPTQ-Int4
```

检查：

```bash
docker run --rm \
  -v /data/agent-security-platform/models:/models:ro \
  crpi-5gm6gpgyiqxur1oj-vpc.cn-beijing.personal.cr.aliyuncs.com/agent_platform/asp_docker:vllm-openai-latest \
  bash -lc 'ls -lh /models/text/Qwen2.5-14B-Instruct-GPTQ-Int4 | head'
```

---

## 7. PostgreSQL 常见故障

### 7.1 修改 `postgres.env` 后不生效

PostgreSQL 官方镜像的初始化变量只在数据目录为空时生效。

如果目录已初始化：

```text
/data/agent-security-platform/services/postgresql/data
```

后续修改这些变量不会自动创建新用户或新库：

```text
POSTGRES_DB
POSTGRES_USER
POSTGRES_PASSWORD
ASP_APP_DB
ASP_APP_USER
ASP_APP_PASSWORD
```

解决方式：

```text
已有数据：用 psql 手动 ALTER / CREATE。
无重要数据：停止容器、清空 data 目录、重新初始化。
```

清空前必须停止容器：

```bash
cd /data/agent-security-platform/compose
docker compose -f docker-compose.postgres.yml down

sudo find /data/agent-security-platform/services/postgresql/data \
  -mindepth 1 \
  -maxdepth 1 \
  -exec rm -rf -- {} +
```

### 7.2 `docker exec psql` 不需要密码

这是因为容器内部本地连接通常走 Unix socket 或本地信任规则。后端通过 TCP 连接时仍需要密码。

强制测试 TCP 密码：

```bash
docker exec -it asp-postgres \
  psql -h 127.0.0.1 -U asp_app -d asp_db
```

---

## 8. 代理与下载排错

### 8.1 当前代理状态

```bash
proxy-status
```

开启：

```bash
proxy-on
```

关闭：

```bash
proxy-off
```

### 8.2 ModelScope 下载

ModelScope 优先直连：

```bash
proxy-off

cd /data/agent-security-platform/tools/modelscope
source .venv/bin/activate

modelscope download \
  --model Qwen/Qwen2.5-14B-Instruct-GPTQ-Int4 \
  --local_dir /data/agent-security-platform/models/text/Qwen2.5-14B-Instruct-GPTQ-Int4

proxy-on
```

### 8.3 GitHub / Hugging Face / Docker Hub

这类海外依赖默认走代理更稳：

```bash
proxy-on
curl -I https://github.com
curl -I https://huggingface.co
curl -I https://registry-1.docker.io/v2/
```

Docker daemon 不读取 shell 的代理变量。如需 Docker daemon 走代理，需要单独配置 systemd drop-in。

---

## 9. 发布检查清单

### 9.1 发布前

```text
确认 Git 分支和 commit。
确认数据库已备份。
确认 env 文件已更新。
确认镜像已 push 到 ACR。
确认 Docker Compose 配置可解析。
确认 /data 剩余空间充足。
```

命令：

```bash
df -hT /data
docker compose -f docker-compose.yml config
```

### 9.2 发布后

```text
docker ps 正常。
PostgreSQL healthy。
vLLM /v1/models 正常。
Backend /healthz 正常。
Backend /readyz 正常。
Gateway 前端可访问。
关键 API 可访问。
```

---

## 10. 安全边界

禁止：

```text
向公网开放 5432。
向公网开放 18000。
向公网开放 10808。
把真实 env 提交到 Git。
把模型权重提交到 Git。
把数据库 data 目录打包进仓库。
runtime-runner 使用 privileged。
runtime-runner 挂载 /var/run/docker.sock。
runtime-runner 发布宿主机随机端口。
在安全组中开放 runtime 动态端口段。
```

允许：

```text
Worker 在必要时挂载 /var/run/docker.sock。
但 Worker 不对外暴露。
Worker 仅创建平台 runtime 容器，不接收用户提交的 Docker 镜像。
Worker 创建的 runtime-runner 仅加入 asp-runtime-net。
runtime-runner 使用容器内固定端口 8000，由 Worker 通过 Docker 内网访问。
runtime-runner 只挂载单次 workdir。
runtime-runner 运行完成后销毁。
```

---

## 11. 清理策略

Runtime 自动清理：

```text
scheduler 会运行 runtime session reaper，定期把超过 expires_at 的 active session 标记为 expired。
backend-worker 会扫描 managedBy=asp-worker 的 runtime 容器。
只有没有 active runtime session 的残留容器会被停止。
API、scheduler、runtime-runner 都不挂载 /var/run/docker.sock；只有 backend-worker 可清理 runtime 容器。
外部 Agent 只访问 /runtime/tasks/{sampleExecutionId}/...，初始 token 只通过 query 交给 gateway。
```

可清理：

```text
/data/agent-security-platform/runtime 下过期 workdir
/data/agent-security-platform/tmp
Docker dangling images
Docker build cache
过期日志
过期备份，按保留策略删除
```

不可随意清理：

```text
/data/docker
/data/agent-security-platform/services/postgresql/data
/data/agent-security-platform/models
/data/agent-security-platform/data/datasets
/data/agent-security-platform/data/uploads
/data/agent-security-platform/artifacts/runs
/data/agent-security-platform/backups
/data/agent-security-platform/env
/data/agent-security-platform/www/frontend/releases 中仍可能回滚的版本
```

慎用：

```bash
docker system prune -a --volumes
```

---

## 12. Agent 操作约束

自动化 Agent 执行部署或维护任务时必须遵守：

```text
删除数据库 data 目录前必须确认 PostgreSQL 容器已停止。
不得删除 /data/docker。
不得删除 /data/agent-security-platform/env。
不得删除 /data/agent-security-platform/models。
不得向公网暴露 vLLM、PostgreSQL、Xray。
修改 Compose 后必须执行 docker compose config。
部署后必须执行健康检查。
执行数据库迁移前必须备份 asp_db。
对 runtime 和 tmp 的清理必须限定路径和保留策略。
```
