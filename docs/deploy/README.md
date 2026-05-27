# WEB 智能体安全自动化测评平台部署文档索引

本目录用于存放平台部署、运行、运维相关文档，供开发人员、运维人员和自动化 Agent 查阅。

## 文档列表

| 文件 | 用途 |
|---|---|
| `01-deployment-architecture.md` | 部署架构、目录规划、服务分层、网络边界、扩展策略 |
| `02-deployment-implementation.md` | 主环境具体部署步骤，包含 PostgreSQL、vLLM、Backend、Worker、Frontend、Gateway |
| `03-operations-runbook.md` | 日常运维、排错、备份、启停、安全边界、Agent 操作约束 |

## 当前主环境状态

最近一次服务器只读检查：`2026-05-26 00:43 CST`。

```text
PostgreSQL：
  容器：asp-postgres
  管理用户：asp_admin
  生产库：asp_db
  生产用户：asp_app
  测试库：test_db
  测试用户：asp_test
  当前状态：容器 healthy；生产库已有后端表，但需按当前代码继续迁移到最新 Alembic head

vLLM：
  容器：asp-vllm
  模型：Qwen2.5-14B-Instruct-GPTQ-Int4
  服务模型名：qwen2.5-14b-gptq-int4
  当前状态：容器运行，GPU 上有 VLLM::EngineCore；当前主要通过 LiteLLM 暴露模型代理

LiteLLM：
  容器：asp-litellm
  宿主机调试入口：http://127.0.0.1:18400/v1
  后端容器入口：http://asp-litellm:4000/v1
  当前状态：容器运行；未带 API key 访问 /v1/models 返回 401

Gateway：
  容器：asp-nginx
  当前状态：容器 healthy，已在 asp-net 中预留 /api/* → backend-api:8000
  注意：后端未部署前 /api/v1/ 会返回 502；/health 或前端 SPA 200 不代表后端 ready

Backend：
  镜像构建：backend/Dockerfile
  Compose 模板：docs/deploy/templates/backend/docker-compose.backend.yml
  Compose .env 模板：docs/deploy/templates/backend/compose.env.example
  生产 env 模板：docs/deploy/templates/backend/backend.env.example
  API upstream：backend-api:8000
  Runtime gateway：/runtime/tasks/* → backend-api:8000
  Worker runtime 网络：asp-runtime-net
  Runtime runner：容器内固定端口 8000，不发布宿主机端口
  当前状态：/data/.../services/backend/compose 与日志目录已落地；后端镜像 tag、真实 .env 值、migration、backend-api、scheduler、worker 尚未完成
```

后端 Docker 部署前必须先补齐或确认：

```text
/data/agent-security-platform/services/backend/compose/docker-compose.yml 已存在
/data/agent-security-platform/services/backend/compose/.env 已存在，但 BACKEND_IMAGE / BACKEND_DATABASE_URL 仍需替换为真实值
/data/agent-security-platform/logs/backend 与 logs/worker 已存在
PostgreSQL compose 已声明 asp-db-net，asp-postgres 重建后仍会加入该网络
Docker 后端运行时必须使用 asp-postgres、asp-litellm 这类容器网络地址；不要依赖 backend.env 中的宿主机 127.0.0.1 联调值
backend-migrate 迁移到当前代码 head
```

## 关键约束

```text
真实 env 不进 Git。
模型权重不进 Git。
数据库 data 不进 Git。
runtime 和 artifacts 不进 Git。
公网只暴露 Gateway。
PostgreSQL、vLLM、Xray 不对公网开放。
runtime runner 不对公网或宿主机端口开放。
只有 backend-worker 挂载 Docker socket。
```
