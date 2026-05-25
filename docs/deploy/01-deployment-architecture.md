# 部署架构与目录规划

> 文件建议路径：`docs/deploy/01-deployment-architecture.md`  
> 适用项目：WEB 智能体安全自动化测评平台  
> 适用环境：阿里云 A10 GPU ECS 单机主环境  
> 技术栈：Vue 3、FastAPI、PostgreSQL、vLLM、Docker Compose、ACR、Caddy/Nginx

---

## 1. 架构结论

本项目当前采用 **单机 Docker Compose 主环境部署**：

```text
用户浏览器
  ↓
公网 IP / 域名
  ↓
Gateway，Caddy 或 Nginx
  ├── 前端静态文件
  └── /api/* → FastAPI Backend
        ├── PostgreSQL
        ├── vLLM OpenAI-compatible API
        ├── Worker 调度接口
        ├── datasets / uploads
        └── artifacts / reports / replay
```

核心原则：

```text
代码放 ~/apps
数据放 /data
真实 env 不进 Git
模型不进 Git
数据库数据不进 Git
评测产物不进 Git
公网只暴露 Gateway
PostgreSQL、vLLM、Backend、Worker 不直接暴露公网
```

当前单机部署不引入 Kubernetes、Docker Swarm、服务网格、完整监控栈或 RDS 强依赖。后续在真实用户、数据不可重跑、需要高可用和自动备份时，再评估 RDS、OSS、Redis、多机部署或 Kubernetes。

---

## 2. 当前服务器基线

当前 ECS 已可作为主部署节点：

```text
OS：Ubuntu 24.04.4 LTS
GPU：NVIDIA A10，显存约 23GiB
Driver：NVIDIA 580.126.09
Docker：Docker Engine 29.3.1
Docker Compose：v5.1.1
Docker Root Dir：/data/docker
数据盘挂载：/data
普通用户：ecs-user，可直接使用 docker
容器 GPU：已验证可用
ACR VPC 拉取：已验证可用
本机代理：Xray，127.0.0.1:10808
```

已完成的基础中间件：

```text
PostgreSQL：
  容器：asp-postgres
  管理库：postgres
  管理用户：asp_admin
  生产库：asp_db
  生产用户：asp_app
  测试库：test_db
  测试用户：asp_test
  监听：127.0.0.1:5432

vLLM：
  容器：asp-vllm
  模型：Qwen2.5-14B-Instruct-GPTQ-Int4
  服务模型名：qwen2.5-14b-gptq-int4
  监听：127.0.0.1:18000 → 容器 8000
  API：/v1/models、/v1/chat/completions 已验证
```

---

## 3. 仓库源码目录

```text
~/apps/
└── agent-security-platform/
    ├── frontend/
    ├── backend/
    ├── docs/
    │   └── deploy/
    ├── deploy/
    │   ├── compose/
    │   ├── env.example/
    │   └── scripts/
    ├── scripts/
    ├── tools/
    ├── README.md
    ├── .env.example
    └── .gitignore
```

职责：

```text
保存 Git 管理的源码、Dockerfile、Compose 模板、脚本模板和文档。
不保存真实密钥。
不保存数据库数据。
不保存模型文件。
不保存上传文件。
不保存评测 runtime 与 artifacts。
```

---

## 4. 服务器运行目录

```text
/data/
├── docker/
└── agent-security-platform/
    ├── compose/
    ├── env/
    │   └── prod/
    ├── www/
    │   └── frontend/
    ├── services/
    │   └── postgresql/
    ├── models/
    │   ├── text/
    │   └── vision/
    ├── cache/
    │   ├── modelscope/
    │   ├── huggingface/
    │   ├── vllm/
    │   ├── uv/
    │   ├── pip/
    │   ├── pnpm/
    │   └── playwright/
    ├── data/
    │   ├── datasets/
    │   ├── dataset-registry/
    │   ├── uploads/
    │   ├── imports/
    │   └── exports/
    ├── runtime/
    ├── artifacts/
    ├── logs/
    ├── backups/
    ├── local-agents/
    └── tmp/
```

说明：

```text
/data/docker
  Docker daemon 数据目录，包括镜像层、容器层、build cache。

/data/agent-security-platform/compose
  生产 Compose 文件与服务编排文件。

/data/agent-security-platform/env/prod
  真实生产环境变量。不进入 Git。

/data/agent-security-platform/services/postgresql/data
  PostgreSQL 数据目录。不可随意删除。

/data/agent-security-platform/models
  模型权重目录。vLLM 只读挂载。

/data/agent-security-platform/cache
  ModelScope、Hugging Face、vLLM、uv、pip、pnpm、Playwright 缓存。

/data/agent-security-platform/data
  业务长期数据：datasets、uploads、imports、exports。

/data/agent-security-platform/runtime
  临时运行目录，评测执行中使用，允许按策略清理。

/data/agent-security-platform/artifacts
  评测证据、报告、trace、screenshot、replay、logs。

/data/agent-security-platform/backups
  PostgreSQL dump、配置备份、重要报告备份。
```

---

## 5. 服务规划

| 服务 | 容器名 | 部署方式 | 公网暴露 | 持久化目录 | 当前状态 |
|---|---|---|---:|---|---|
| Gateway | `asp-gateway` | Docker Compose | 是，80/443 | `services/caddy` 或 `services/nginx` | 待部署 |
| Frontend | 无固定容器 | 静态 release + Gateway | 通过 Gateway | `www/frontend` | 待部署 |
| Backend API | `backend-api` | Docker Compose | 否 | 无状态，挂载 data/runtime/logs | 模板已提供 |
| Backend Scheduler | `asp-backend-scheduler` | Docker Compose | 否 | 主要依赖 DB | 模板已提供 |
| Backend Worker | `asp-backend-worker-*` | Docker Compose | 否 | 挂载 data/runtime/logs 与 Docker socket | 模板已提供 |
| Backend Migration | `asp-backend-migrate` | Docker Compose 一次性任务 | 否 | 无持久化 | 模板已提供 |
| PostgreSQL | `asp-postgres` | Docker Compose | 否 | `services/postgresql/data` | 已部署 |
| vLLM | `asp-vllm` | Docker Compose + GPU | 否 | `models`、`cache/vllm` | 已部署 |
| Runtime Runner | 临时容器 | Worker 创建 | 否 | 单次 workdir | 待部署 |
| Redis | `asp-redis` | Docker Compose | 否 | `services/redis/data` | 可选 |

---

## 6. 网络与端口规划

### 6.1 阿里云安全组

长期开放：

```text
22/tcp
80/tcp
443/tcp
```

不要开放：

```text
5432/tcp     PostgreSQL
8000/tcp     FastAPI
18000/tcp    vLLM
5173/tcp     Vite dev server
10808/tcp    Xray 本机代理
```

### 6.2 宿主机本地端口

```text
127.0.0.1:5432    PostgreSQL
127.0.0.1:18000   vLLM OpenAI-compatible API
127.0.0.1:10808   Xray mixed proxy
```

### 6.3 Compose 内部访问

```text
asp-net:      nginx → backend-api:8000
asp-db-net:   backend-api / scheduler / worker / migrate → asp-postgres:5432
asp-ai-net:   backend-api / worker → asp-litellm:4000 或 asp-vllm:8000
asp-runtime-net: backend-worker → 一次性 runtime runner
```

---

## 7. PostgreSQL 设计

当前采用：

```text
一个 PostgreSQL 容器
一个 PostgreSQL 实例
一个管理用户
两个业务数据库
两个业务用户
```

命名：

```text
容器：asp-postgres
管理库：postgres
管理用户：asp_admin
生产库：asp_db
生产用户：asp_app
测试库：test_db
测试用户：asp_test
```

连接策略：

```text
生产后端只连接 asp_db / asp_app。
测试后端只连接 test_db / asp_test。
管理用户 asp_admin 只用于建库、建用户、迁移维护和备份。
不推荐长期使用单一用户同时访问生产库和测试库。
```

---

## 8. vLLM 设计

当前采用：

```text
容器：asp-vllm
镜像：crpi-5gm6gpgyiqxur1oj-vpc.cn-beijing.personal.cr.aliyuncs.com/agent_platform/asp_docker:vllm-openai-latest
模型：Qwen2.5-14B-Instruct-GPTQ-Int4
服务模型名：qwen2.5-14b-gptq-int4
量化：GPTQ Int4
端口：127.0.0.1:18000 → 容器 8000
```

后端访问：

```env
LLM_JUDGE_PROVIDER=litellm
LLM_BASE_URL=http://vllm:8000/v1
LLM_DEFAULT_MODEL=qwen2.5-14b-gptq-int4
```

宿主机测试：

```env
LLM_JUDGE_PROVIDER=litellm
LLM_BASE_URL=http://127.0.0.1:18000/v1
LLM_DEFAULT_MODEL=qwen2.5-14b-gptq-int4
```

当前参数：

```text
--quantization gptq
--gpu-memory-utilization 0.85
--max-model-len 8192
```

如果后续出现 OOM：

```text
优先改为 --max-model-len 4096
其次改为 --gpu-memory-utilization 0.80
```

---

## 9. ACR 镜像策略

仓库职责：

```text
agent_platform/asp_docker
  基础镜像、中间件镜像、CUDA、PostgreSQL、vLLM、Caddy/Nginx、Redis。

agent_platform/asp_code
  项目业务镜像：backend、worker、runtime-runner、frontend-build。
```

推荐流程：

```text
本地电脑或可访问 Docker Hub 的机器：
  docker pull 官方镜像
  docker tag 到 ACR 公网地址
  docker push 到 ACR

ECS：
  docker login ACR VPC 域名
  docker pull ACR VPC 镜像地址
  docker compose 使用 ACR VPC 镜像地址
```

---

## 10. 代理与缓存策略

交互式终端允许默认启用代理：

```text
HTTP_PROXY=http://127.0.0.1:10808
HTTPS_PROXY=http://127.0.0.1:10808
```

但不做系统级全局代理。

推荐：

```text
~/.asp-cache-env
  配置 ModelScope、Hugging Face、vLLM、uv、pip 缓存目录。

~/.proxy-env
  配置本机 Xray 代理与 NO_PROXY。

proxy-on / proxy-off / proxy-status
  在交互式终端中显式切换。
```

ModelScope 下载模型优先直连；GitHub、Hugging Face、Docker Hub、OpenAI API 默认走代理更稳。

---

## 11. 最终目标状态

```text
公网只看到 Gateway。
Gateway 反向代理 Backend。
Backend 连接 PostgreSQL 和 vLLM。
Scheduler 推进 run 生命周期、dataset 阶段和报告聚合。
Sample Worker 领取并执行 sample_execution，内部低并发，依靠实例数横向扩容。
runtime-runner 由 Worker 按单样本启动，隔离执行浏览器/Agent 任务。
PostgreSQL 保存结构化业务数据。
vLLM 提供本地模型推理。
runtime 保存临时执行上下文。
artifacts 保存长期评测证据。
所有长期数据在 /data。
所有源码在 ~/apps。
```
