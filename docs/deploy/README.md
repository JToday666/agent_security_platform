# WEB 智能体安全自动化测评平台部署文档索引

本目录用于存放平台部署、运行、运维相关文档，供开发人员、运维人员和自动化 Agent 查阅。

## 文档列表

| 文件 | 用途 |
|---|---|
| `01-deployment-architecture.md` | 部署架构、目录规划、服务分层、网络边界、扩展策略 |
| `02-deployment-implementation.md` | 主环境具体部署步骤，包含 PostgreSQL、vLLM、Backend、Worker、Frontend、Gateway |
| `03-operations-runbook.md` | 日常运维、排错、备份、启停、安全边界、Agent 操作约束 |

## 当前主环境状态

```text
PostgreSQL：
  容器：asp-postgres
  管理用户：asp_admin
  生产库：asp_db
  生产用户：asp_app
  测试库：test_db
  测试用户：asp_test

vLLM：
  容器：asp-vllm
  模型：Qwen2.5-14B-Instruct-GPTQ-Int4
  服务模型名：qwen2.5-14b-gptq-int4

LiteLLM：
  容器：asp-litellm
  宿主机调试入口：http://127.0.0.1:18400/v1
  后端容器入口：http://asp-litellm:4000/v1

Backend：
  镜像构建：backend/Dockerfile
  Compose 模板：docs/deploy/templates/backend/docker-compose.backend.yml
  Compose .env 模板：docs/deploy/templates/backend/compose.env.example
  生产 env 模板：docs/deploy/templates/backend/backend.env.example
  API upstream：backend-api:8000
  Worker runtime 网络：asp-runtime-net
  Runtime runner：容器内固定端口 8000，不发布宿主机端口
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
