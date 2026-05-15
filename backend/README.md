# Backend README

## 1. 项目定位

`backend/` 是 Agent Security Platform 的后端服务，基于 FastAPI + SQLAlchemy + PostgreSQL。

README 只维护当前状态、启动验证入口、核心约束和文档索引。后端实现细节、领域规则、数据结构、接口索引和待办事项分别维护在 `backend/docs/` 与 `backend/TODO.md`；`share/` 下材料仅作为跨端沟通参考，不作为后端实现真相源。

## 2. 当前能力与目录

当前已开放接口：

- `/api/v1/auth/*`
- `/api/v1/user/*`
- `/api/v1/datasets/*`
- `/api/v1/agents/*`
- `/api/v1/evaluations/*`
- `/api/v1/evaluations/{evaluationId}/score`
- `/api/v1/evaluations/{evaluationId}/score/recalculate`
- `/api/v1/difficulty/*`
- `/api/v1/leaderboards/*`

当前已具备的后端基础：

- 统一响应封装：`{ code, data, message }`
- 后端国际化运行时：`X-App-Locale` 请求级 locale 上下文、JSON 响应 `Content-Language` 与 `Vary: X-App-Locale`、异常统一翻译入口
- 统一 DB Session、登录态依赖与全局异常处理
- Alembic 迁移链路
- 数据集元数据维护、样本标准化与导入链路
- Agent 模板、注册、详情、列表、真实轻量验证、归档与凭据脱敏存储
- `external_agent_api` 调用链路、`synthetic_local` dispatch 闭环、基础产物采集和任务级摘要报告
- 结构化 oracle 执行、`execution_summaries` 汇总、评测评分重算/查询、动态难度版本重算/发布、排行榜快照
- Agent 出站 HTTP 默认 SSRF 防护：仅允许 `http/https`，默认拒绝 localhost、回环、内网、链路本地、保留地址，并逐跳校验重定向
- 运行时目录、上传目录、凭证目录统一收口到仓库根目录 `var/backend/`

核心目录：

- `app/platform/`：配置、DB、响应封装、异常、鉴权基础、凭据存储、共用规则的平台内核
- `app/modules/`：按业务域组织的 `router / service / repository / schemas`
- `app/worker/`：任务领取、执行编排、oracle 判定、报告聚合
- `app/worker/runtime/`：runtime 准备、调度适配器、产物收集
- `app/models/`：SQLAlchemy ORM 模型与 Alembic 发现入口
- `alembic/`：数据库迁移
- `scripts/`：数据导入、联调和烟测脚本
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

备用启动：

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

自动化测试：

```bash
uv run pytest -q
```

按分层目录执行：

```bash
uv run pytest tests/api tests/modules tests/worker tests/scripts -q
```

查看后端与脚本覆盖明细：

```bash
uv run pytest --cov=app --cov=scripts --cov-report=term-missing
```

后端国际化运行时定向验证：

```bash
uv run pytest tests/modules/platform/test_i18n.py tests/modules/platform/test_exception_handlers.py tests/api/test_contracts.py -q
uv run pytest tests/modules/agents/test_service.py tests/modules/auth/test_service.py tests/modules/user/test_service.py tests/modules/evaluations/test_validation.py tests/modules/evaluations/test_mappers.py tests/modules/evaluations/test_service.py tests/modules/scoring/test_service.py tests/modules/difficulty/test_service.py tests/modules/leaderboards/test_service.py tests/modules/datasets/test_service.py tests/modules/datasets/test_metadata_registry.py -q
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

真实 HTTP 冒烟需要先启动 API：

```bash
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

另开终端执行：

```bash
uv run python scripts/qa/http_smoke_check.py --base-url http://127.0.0.1:8000
```

本地真实 run 联调推荐使用脚本化入口：

```bash
uv run python scripts/qa/e2e_local_run.py --spawn-services
```

该脚本会自动完成以下检查：

- 确认数据库与 Alembic revision 可用
- 确认 `B2_cloud_file_modification` 数据集已有可执行样本，必要时自动导入元数据与样本
- 自动启动本地 API 与 worker
- 注册测试用户、注册/验证 Agent、提交任务、轮询详情直至终态
- 校验运行产物至少包含 `event_log`、`compile_result`、`replay_result`

当前联调能力边界：

- 默认脚本化链路优先验证 `synthetic_local` runtime 闭环；外部 API Agent 主链已接入，但需要可访问的真实 Agent 服务
- Docker 调用链当前不开放
- 评分可在任务终态汇总时生成，也可通过 `POST /api/v1/evaluations/{evaluationId}/score/recalculate` 重算；详情接口会返回已写入评分
- `run_reports` 当前稳定返回 `summary_json` 摘要，`report_uri` 仍为空
- 当前还没有样本级 execution 查询接口

## 5. 核心约束

- 新增 API 路由使用 `/api/v1` 前缀
- 业务响应统一使用 `{ code, data, message }`
- 后端响应语言只认 `X-App-Locale`；`Accept-Language` 仅作为前端或网关生成 `X-App-Locale` 的输入来源
- JSON 响应统一返回 `Content-Language` 与 `Vary: X-App-Locale`
- 复用 `app.platform.auth.get_db` 注入 DB Session
- 登录态依赖使用 `app.modules.auth.dependencies.get_current_user`
- 统一通过 `app.platform.http.success_payload` 返回成功 envelope
- 业务异常优先抛出 `app.platform.errors` 下的领域异常
- 数据库结构变更必须通过 Alembic 迁移交付
- 新增模型后先注册到 `app/models/__init__.py`
- 新增环境变量必须在 `app/platform/config.py` 中强类型声明

## 6. 文档索引

仓库级协作规范：

- [AGENTS](../AGENTS.md)

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
