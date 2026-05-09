# Agent Security Platform

Agent Security Platform 是面向 Agent API 的安全测试平台仓库，包含 Vue 前端控制台、FastAPI 后端服务、PostgreSQL 轮询 worker，以及前后端共享接口契约。

## 能力范围

- 公共浏览：首页、数据集目录、数据集详情、排行榜、联系页、404。
- 账号：登录、注册、登录态恢复、个人资料、头像上传、401 未授权回跳。
- Agent：注册、管理、详情、验证、归档、复制新建。
- 提交评测：API Agent 选择、数据集选择、参数校验、提交前预检查、确认提交、草稿保持。
- 评测：历史列表、趋势分析、详情、评分报告、代表样本证据、样本明细下载入口、暂停、恢复、终止、取消。
- 排行榜：读取当前后端排行榜，展示第一名，支持综合分、安全能力、高难分和风险分排序。
- 运行模式：真实后端 API 与前端 Mock API。

## 仓库结构

| 路径        | 职责                                                                                                                        |
| ----------- | --------------------------------------------------------------------------------------------------------------------------- |
| `frontend/` | Vue + TypeScript 前端工程，包含页面、状态组合、共享组件体系（含玻璃态等现代UI隐喻与微交互规范）、前端 Mock API 和前端文档。 |
| `backend/`  | FastAPI 后端、数据库模型、业务模块、worker、迁移和后端测试。                                                                |
| `share/`    | 前后端接口契约和补充说明。                                                                                                  |
| `docs/`     | 项目级设计说明、任务资料和参考文档。                                                                                        |
| `README.md` | 仓库入口、运行方式和文档入口。                                                                                              |

## 前端环境

前端在 `frontend/` 目录运行，Node.js 与 pnpm 要求以 `frontend/package.json` 为准。

生产构建使用 Vite/Rolldown。`pnpm build` 会执行类型检查和生产构建，常规安装使用 `pnpm install --frozen-lockfile` 以保证依赖版本可复现。

常用环境变量：

| 变量                   | 示例                    | 说明                              |
| ---------------------- | ----------------------- | --------------------------------- |
| `VITE_API_BASE_URL`    | `/api/v1`               | 前端运行时 API 基地址。           |
| `VITE_BACKEND_TARGET`  | `http://127.0.0.1:8000` | Vite 开发代理目标。               |
| `VITE_ENABLE_API_MOCK` | `false`                 | `true` 时使用前端 Mock 数据链路。 |

本地联调真实后端：

```env
VITE_API_BASE_URL=/api/v1
VITE_BACKEND_TARGET=http://127.0.0.1:8000
VITE_ENABLE_API_MOCK=false
```

脱离后端演示前端流程：

```env
VITE_ENABLE_API_MOCK=true
```

## 后端环境

后端在 `backend/` 目录运行，Python 与 uv 配置以后端文件为准。

常用环境变量：

| 变量                | 示例                      | 说明               |
| ------------------- | ------------------------- | ------------------ |
| `PROJECT_NAME`      | `Agent Security Platform` | FastAPI 应用标题。 |
| `FASTAPI_HOST`      | `127.0.0.1`               | 本地监听地址。     |
| `FASTAPI_PORT`      | `8000`                    | 本地监听端口。     |
| `POSTGRES_HOST`     | `localhost`               | PostgreSQL 主机。  |
| `POSTGRES_PORT`     | `5432`                    | PostgreSQL 端口。  |
| `POSTGRES_DB`       | `<your_db_name>`          | 数据库名。         |
| `POSTGRES_USER`     | `postgres`                | 数据库用户名。     |
| `POSTGRES_PASSWORD` | `<your_db_password>`      | 数据库密码。       |
| `SQLALCHEMY_ECHO`   | `false`                   | SQL 日志开关。     |

## 启动

启动后端 API：

```bash
cd backend
uv sync
uv run alembic upgrade head
uv run python run.py
```

启动 worker：

```bash
cd backend
uv run python worker.py
```

启动前端：

```bash
cd frontend
pnpm install --frozen-lockfile
pnpm dev
```

仅在前端依赖声明变化或 `pnpm-lock.yaml` 缺失时，由维护者运行 `pnpm install --no-frozen-lockfile` 重新生成锁文件；锁文件提交后，日常开发和 CI 继续使用 `pnpm install --frozen-lockfile`。

常用入口：

- 前端开发地址：以 Vite 终端输出为准，常见为 `http://127.0.0.1:5173`
- OpenAPI：`http://127.0.0.1:8000/docs`
- API v1：`http://127.0.0.1:8000/api/v1/`

## 验证

前端：

```bash
cd frontend
pnpm test
pnpm type-check
pnpm build
```

后端：

```bash
cd backend
uv run pytest -q
```

真实 HTTP 冒烟需要后端 API 和数据库处于可用状态：

```bash
cd backend
uv run python scripts/http_smoke_check.py --base-url http://127.0.0.1:8000
```

## 文档入口

- [frontend/README.md](./frontend/README.md)
- [前端文档地图](./frontend/docs/01-总览/文档地图.md)
- [前端架构说明](./frontend/docs/01-总览/前端架构说明.md)
- [排行榜接口说明](./share/leaderboard接口.md)
- [关键链路说明](./frontend/docs/04-流程/关键链路说明.md)
- [backend/README.md](./backend/README.md)
- [后端文档地图](./backend/docs/01-总览/文档地图.md)
- [后端架构说明](./backend/docs/01-总览/后端架构说明.md)
- [API 接口协议总表](./share/API接口协议.md)
- [Agent 接口补充说明](./share/agent接口.md)
- [提交接口补充说明](./share/submit接口.md)
- [报告接口补充说明](./share/report接口.md)
