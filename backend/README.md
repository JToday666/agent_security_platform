# Backend README

## 1. 项目定位

`backend/` 是 Agent Security Platform 的后端服务，基于 FastAPI + SQLAlchemy + PostgreSQL。

当前仓库已落地三类能力：

- 用户认证与用户资料接口
- 数据集查询、Agent 注册验证、评测创建、评测详情与动作控制接口
- 外部 API Agent 调用与 `synthetic_local` 本地闭环、基础产物采集和任务级摘要报告

README 只描述当前状态。后端实现细节、领域说明和待办事项在独立文档中维护；`share/` 下材料仅作为前后端沟通参考，不作为后端实现真相源。

## 2. 当前能力与目录

当前已开放接口：

- `/api/v1/auth/*`
- `/api/v1/user/*`
- `/api/v1/datasets/*`
- `/api/v1/agents/*`
- `/api/v1/evaluations/*`

当前已具备的后端基础：

- 统一响应封装：`{ code, data, message }`
- 统一 DB Session、鉴权依赖与全局异常处理
- Alembic 迁移链路
- 独立 worker 轮询执行链路
- `var/backend/workdir` 工作目录准备、probe backend 拉起、基础 artifact 收集
- `external_agent_api` 调用链路、`synthetic_local` dispatch 闭环与 `run_reports.summary_json` 摘要写回
- Agent 出站 HTTP 默认 SSRF 防护：仅允许 `http/https`，默认拒绝 localhost、回环、内网、链路本地、保留地址，并逐跳校验重定向
- 运行时目录、上传目录、凭证目录统一收口到仓库根目录 `var/backend/`

核心目录：

- `app/platform/`：配置、DB、响应封装、异常、鉴权、凭据存储、共用规则的平台内核
- `app/shared/`：历史兼容导出层，新代码不再直接依赖
- `app/modules/`：按业务域组织的 `router / service / repository / schemas`
- `app/worker/`：任务领取、执行编排、报告聚合
- `app/worker/runtime/`：runtime 准备、调度适配器、产物收集
- `app/`：后端业务代码总入口
- `alembic/`：数据库迁移
- `data/`：真实样本与各风险子类 runtime 目录
- `data/metadata/`：版本化数据集元数据 JSON 真源
- `var/backend/`：运行时目录（上传、凭证、worker workdir）
- `docs/`：后端内部说明与规范文档

## 3. 快速启动

以下命令都在 `backend/` 目录执行。

```bash
cp .env.example .env
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

也可使用：

```bash
uv run python run.py
```

worker 启动：

```bash
uv run python worker.py
```

常用入口：

- OpenAPI：`http://127.0.0.1:8000/docs`
- 根路径：`GET /`
- API 根路径：`GET /api/`
- API v1 根路径：`GET /api/v1/`

## 4. 检查与验证

所有检查命令都必须在 `backend/` 目录执行。

依赖与迁移：

```bash
uv sync
uv run alembic upgrade head
uv run alembic current
```

数据库连通性检查：

```bash
uv run python - <<'PY'
import asyncio
from sqlalchemy import text
from app.platform.db.session import AsyncSessionLocal, engine

async def main() -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT 1 AS ok, current_database() AS db, current_user AS db_user"))
        print(result.one())
    await engine.dispose()

asyncio.run(main())
PY
```

自动化测试：

```bash
uv run pytest -q
```

说明：

- 当前仓库的测试主入口是 `pytest`；`python -m unittest discover` 实际不会发现这些测试文件。

按分层目录执行：

```bash
uv run pytest tests/api tests/modules tests/worker tests/scripts -q
```

查看后端与脚本覆盖明细：

```bash
uv run pytest --cov=app --cov=scripts --cov-report=term-missing
```

真实 HTTP 冒烟：

```bash
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

另开一个终端，在同样的 `backend/` 目录执行：

```bash
uv run python scripts/qa/http_smoke_check.py --base-url http://127.0.0.1:8000
```

本地真实 run 联调：

推荐优先直接执行脚本化联调：

```bash
uv run python scripts/qa/e2e_local_run.py --spawn-services
```

该脚本会自动完成以下检查：

- 确认数据库与 Alembic revision 可用
- 确认 `B2_cloud_file_modification` 数据集已有可执行样本；若缺失则自动导入元数据与样本
- 自动启动本地 API 与 worker
- 注册测试用户、提交任务、轮询详情直至终态
- 校验运行产物至少包含 `event_log`、`compile_result`、`replay_result`

当前联调能力边界：

- 默认脚本化链路优先验证 `synthetic_local` runtime 闭环；外部 API Agent 主链已接入，但需要可访问的真实 Agent 服务
- Docker 调用链当前不开放
- 详情接口里的 `score` 当前仍为 `null`
- `run_reports` 当前只返回摘要，`report_uri` 仍为空
- 当前还没有样本级 execution 查询接口

如果需要手工分步联调，可按下面流程执行。

1. 安装依赖并迁移数据库

```bash
uv sync
uv run alembic upgrade head
```

2. 准备并导入数据集元数据与 B2 样本

推荐直接使用顶层脚本完成“识别输入类型 -> 必要时标准化 -> 回写/补齐 `data/metadata` -> 导入元数据 -> 导入样本”整条链路：

```bash
uv run python scripts/import_datasets.py --sample-root ./data/02_Integrity/B2_Cloud_File_Modification
```

说明：

- `scripts/import_datasets.py` 会自动识别 raw / standard 两类样本目录
- raw 输入会先标准化，再回写 `data/metadata/` JSON 真源并继续导入
- 如需分步执行，使用 `scripts/datasets/normalize_samples.py`、`sync_metadata_from_samples.py`、`import_metadata.py`、`import_samples.py`
- `scripts/qa/e2e_local_run.py` 在本地联调时会按需要自动导入 `backend/data/02_Integrity/B2_Cloud_File_Modification`

3. 安装 Playwright Chromium

```bash
uv run playwright install chromium
```

4. 启动 API 与 worker

```bash
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

另开一个终端：

```bash
uv run python worker.py
```

5. 注册用户

- 路由：`POST /api/v1/auth/register`
- 请求示例：

```json
{
  "username": "local_e2e_user",
  "email": "local_e2e@example.com",
  "password": "secret123"
}
```

- 响应示例：

```json
{
  "code": 0,
  "data": {
    "token": "<jwt>",
    "user": {
      "id": 1,
      "username": "local_e2e_user",
      "email": "local_e2e@example.com"
    }
  },
  "message": "success"
}
```

6. 注册 API Agent 并提交真实 run

- 注册路由：`POST /api/v1/agents`
- 验证路由：`POST /api/v1/agents/{agentId}/verify`
- 提交路由：`POST /api/v1/evaluations`
- Agent 注册请求示例：

```json
{
  "templateId": "http_submit_poll_basic",
  "name": "local-e2e-agent",
  "description": "local worker e2e",
  "invokeMode": "sync_response",
  "connection": {
    "baseUrl": "https://agent.example.com",
    "invokePath": "/run",
    "requestTimeoutSeconds": 30
  },
  "auth": {"type": "bearer", "config": {"token": "sk-demo"}},
  "platformInputMapping": {
    "task": "prompt",
    "entryUrl": "url",
    "timeoutSeconds": "timeout_sec",
    "sampleId": "sample_id",
    "evaluationId": "evaluation_id",
    "maxSteps": "max_steps"
  },
  "taskRenderMode": "goal_only",
  "customRequestBody": {},
  "requestOptions": {},
  "platformOutputMapping": {"status": "status", "finalAnswer": "answer", "errorMessage": "error"},
  "terminalStatuses": ["completed", "failed"],
  "successStatuses": ["completed"]
}
```

- Evaluation 提交请求示例：

```json
{
  "submitMethod": "api",
  "agentId": "agt_ab12cd34ef56",
  "parameters": {
    "difficulty": 0.35,
    "timeoutMinutes": 20,
    "maxSteps": 30
  },
  "publicToLeaderboard": false,
  "datasetIds": ["B2_cloud_file_modification"],
  "requestId": "local_e2e_20260417_000001"
}
```

说明：
- 当前仓库内 `B2_cloud_file_modification` 的活跃样本难度主要落在 `0.35 / 0.675 / 1.0`。
- 如果你直接手工提交 `difficulty=0.5`，现有提交服务会返回“当前条件下没有可执行样本”。
- `scripts/qa/e2e_local_run.py` 会自动从默认 `0.5` 回退到最近可执行难度桶；手工联调建议直接使用 `0.35`。

- 响应示例：

```json
{
  "code": 0,
  "data": {
    "evaluationId": "eval_20260417_000001_ab12cd",
    "submitMethod": "api",
    "agentId": "agt_ab12cd34ef56",
    "status": "pending",
    "createdAt": "2026-04-17T00:00:01Z"
  },
  "message": "success"
}
```

Agent 验证通过后状态会变为 `active`。只有 `active` Agent 可以用于 `POST /api/v1/evaluations` 创建评测；评测创建时会把非敏感 Agent 配置冻结到 `test_runs.execution_config.frozenAgentSnapshot`，后续执行不依赖 Agent 详情的可变读取。

7. 轮询评测详情直到完成

- 路由：`GET /api/v1/evaluations/{evaluationId}`
- 响应中重点关注：
  - `status`
  - `progress.percent`
  - `finalizationReason`
  - `report.summary`
- 响应示例：

```json
{
  "code": 0,
  "data": {
    "evaluationId": "eval_20260417_000001_ab12cd",
    "status": "completed",
    "progress": {
      "percent": 100,
      "totalDatasetCount": 1,
      "completedDatasetCount": 1,
      "runningDatasetId": null,
      "runningDatasetName": null,
      "pauseDeadlineAt": null,
      "statusText": "评测已完成。"
    },
    "controls": {
      "canPause": false,
      "canResume": false,
      "canTerminate": false,
      "canCancel": false,
      "pauseUsed": false
    },
    "finalReportAvailable": true,
    "finalizationReason": "completed",
    "report": {
      "reportStatus": "available",
      "summary": {
        "totalSamples": 1,
        "completedSamples": 1,
        "taskCompletedCount": 0,
        "harmDetectedCount": 0,
        "failedCount": 0,
        "byRiskCategory": [],
        "byRiskLevel": [],
        "byAttackLevel": []
      },
      "reportUri": null
    }
  },
  "message": "success"
}
```

8. 查看运行时产物目录

```bash
ls ../var/backend/workdir/<execution_id>/project/agent_runtime/runs/<environment_ref>/
```

说明：

- 当前可稳定看到的核心产物是 `events.jsonl`、`compile_result.json`、`replay_result.json`、`report.html` 等 runtime 基础证据；外部 API Agent 链路还会按响应映射写入执行摘要
- 更丰富的网络请求、工具调用和独立报告导出仍在后续待办中

也可以直接执行脚本化联调：

```bash
uv run python scripts/qa/e2e_local_run.py --spawn-services
```

## 5. 核心约束

- 新增 API 路由使用 `/api/v1` 前缀
- 业务响应统一使用 `{ code, data, message }`
- 复用 `app.platform.auth` 中的 `get_db`，登录态依赖在 `app.modules.auth.dependencies`
- 统一通过 `app.platform.http` 返回成功 envelope，通过 `app.platform.errors` 抛出业务异常
- 数据库结构变更必须通过 Alembic 迁移交付
- 新增模型后先注册到 `app/models/__init__.py`

## 6. 文档索引

后端内部文档：

- [文档地图](./docs/01-总览/文档地图.md)
- [后端架构说明](./docs/01-总览/后端架构说明.md)
- [后端模块实现清单](./docs/01-总览/后端模块实现清单.md)
- [测评领域说明](./docs/02-领域/测评领域说明.md)
- [枚举与状态约定](./docs/02-领域/枚举与状态约定.md)
- [数据库说明](./docs/03-数据/数据库说明.md)
- [样本导入说明](./docs/03-数据/样本导入说明.md)
- [数据集元数据维护说明](./docs/03-数据/数据集元数据维护说明.md)
- [接口索引与实现状态](./docs/04-接口/接口索引与实现状态.md)
- [响应与错误码约定](./docs/05-规范/响应与错误码约定.md)
- [文档维护约定](./docs/05-规范/文档维护约定.md)

跨端沟通参考：

- [API 接口协议总表](../share/API接口协议.md)
- [用户接口补充说明](../share/user接口.md)
- [数据集与提交接口补充说明](../share/database&submit接口.md)
- [评测记录与报告接口补充说明](../share/evaluations接口.md)

待办事项：

- [TODO](./TODO.md)
