# Backend README

## 1. 项目定位

`backend/` 是 Agent Security Platform 的后端服务，基于 FastAPI + SQLAlchemy + PostgreSQL。

当前仓库已落地两类能力：

- 用户认证与用户资料接口
- 测评样本、测评任务、执行记录、判定结果、报告相关的数据模型与迁移

README 只描述当前状态。跨端接口契约、后端内部说明和待办事项分别在独立文档中维护。

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
- 运行时目录、上传目录、凭证目录统一收口到 `runtime/`

核心目录：

- `app/shared/`：配置、DB、响应封装、异常、鉴权、共用规则
- `app/modules/`：按业务域组织的 `router / service / repository / schemas`
- `app/worker/`：任务领取、执行编排、报告聚合
- `app/`：后端业务代码总入口
- `alembic/`：数据库迁移
- `datasets_demo/`：示例样本目录
- `environments/`：隔离执行目录
- `runtime/`：运行时目录（上传、凭证、worker workdir）
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

## 4. 核心约束

- 新增 API 路由使用 `/api/v1` 前缀
- 业务响应统一使用 `{ code, data, message }`
- 复用 `app.shared.auth` 中的 `get_db`、`get_current_user`
- 统一通过 `app.shared.http` 返回成功 envelope，通过 `app.shared.errors` 抛出业务异常
- 数据库结构变更必须通过 Alembic 迁移交付
- 新增模型后先注册到 `app/models/__init__.py`

## 5. 文档索引

后端内部文档：

- [文档地图](./docs/01-总览/文档地图.md)
- [后端架构说明](./docs/01-总览/后端架构说明.md)
- [测评领域说明](./docs/02-领域/测评领域说明.md)
- [枚举与状态约定](./docs/02-领域/枚举与状态约定.md)
- [数据库说明](./docs/03-数据/数据库说明.md)
- [样本导入说明](./docs/03-数据/样本导入说明.md)
- [接口索引与实现状态](./docs/04-接口/接口索引与实现状态.md)
- [响应与错误码约定](./docs/05-规范/响应与错误码约定.md)
- [文档维护约定](./docs/05-规范/文档维护约定.md)

跨端接口契约：

- [用户接口](../share/user接口.md)
- [数据集与提交接口](../share/database&submit接口.md)
- [评测记录与报告接口](../share/evaluations接口.md)

待办事项：

- [TODO](./TODO.md)
