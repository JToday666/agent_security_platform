# README

## 架构说明

### 项目结构

```markdown
backend/
├── alembic/                 # Alembic 迁移目录
│   ├── env.py               # Alembic 环境配置
│   ├── script.py.mako       # Revision 模板
│   └── versions/            # 迁移版本文件
├── alembic.ini              # Alembic 配置文件
├── app/
│   ├── main.py              # 应用入口
│   ├── api/
│   │   ├── router.py        # 路由配置
│   │   ├── deps.py          # 依赖注入
│   │   └── v1/
│   │       ├── api.py       # API 版本管理
│   │       └── endpoints/   # 具体端点实现
│   ├── core/
│   │   └── config.py        # 配置管理
│   ├── crud/                # 数据库操作层
│   ├── db/
│   │   ├── base.py          # 数据库基础配置
│   │   └── session.py       # 数据库会话
│   ├── models/              # 数据库模型
│   └── schemas/             # Pydantic 数据模型
├── .env.example             # 环境变量示例
├── pyproject.toml           # uv / 项目依赖配置
├── uv.lock                  # uv 锁定文件
├── requirements.txt         # 兼容安装方式的依赖列表
├── run.py                   # 启动脚本
└── README.md                # 项目说明
```

### 技术栈

- **框架**：FastAPI
- **服务器**：Uvicorn
- **数据验证**：Pydantic
- **数据库**：SQLAlchemy + asyncpg

## 后端运行方法

以下命令均在 `backend` 目录下执行。

### 推荐方式：使用 uv

前置条件：

- Python 3.12+
- 已安装 `uv`
- 本地 PostgreSQL 已启动

可先执行下面的命令确认 `uv` 已安装：

```shell
uv --version
```

#### 1. 准备环境变量

先复制环境变量示例文件，再按本地数据库配置修改 `.env`：

```powershell
Copy-Item .env.example .env
```

如果使用的是 macOS / Linux：

```bash
cp .env.example .env
```

`.env` 中至少需要确认以下配置：

- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `FASTAPI_HOST`
- `FASTAPI_PORT`

#### 2. 安装依赖

```shell
uv sync
```

#### 3. 启动服务

直接使用 `uvicorn` 启动：

```shell
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

或使用项目自带脚本启动：

```shell
uv run python run.py
```

说明：

- `uv run python run.py` 会读取 `.env` 中的 `FASTAPI_HOST` 和 `FASTAPI_PORT`
- 上面的 `uvicorn` 命令适合临时指定 host / port
- `--reload` 适合开发环境，生产环境不要开启

### 兼容方式：使用 python / uvicorn

如果暂时不使用 `uv`，也可以继续使用现有方式：

```shell
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

或者直接运行：

```shell
python run.py
```

说明：

- `python run.py` 同样会读取 `.env` 中的 `FASTAPI_HOST` 和 `FASTAPI_PORT`
- 如果 `.env` 中配置了其他端口，请按实际端口访问接口

### IDE 配置

可以直接在 VS Code / PyCharm 中运行 `run.py`，建议使用 `backend/.venv` 作为解释器。

## 数据库迁移

数据库 schema 变更统一通过 Alembic 管理，应用启动时不会自动建表或自动迁移。

### 首次初始化

确保 `.env` 中的 PostgreSQL 连接信息正确后，在 `backend` 目录执行：

```shell
uv run alembic upgrade head
```

如果暂时不使用 `uv`，也可以执行：

```shell
python -m alembic upgrade head
```

### 常用命令

创建新迁移：

```shell
uv run alembic revision --autogenerate -m "message"
```

查看当前迁移版本：

```shell
uv run alembic current
```

查看迁移历史：

```shell
uv run alembic history
```

执行迁移到最新版本：

```shell
uv run alembic upgrade head
```

回滚一个版本：

```shell
uv run alembic downgrade -1
```

回滚到初始状态：

```shell
uv run alembic downgrade base
```

### 使用约束

- 所有迁移命令都在 `backend` 目录执行
- 新增模型后，先在 `app/models/__init__.py` 注册，再执行 `revision --autogenerate`
- 不要在应用代码里调用 `create_all`，所有 schema 变更必须走 migration

## 后端测试

以下示例默认服务运行在 `http://127.0.0.1:8000`。

### POST /auth/register

```txt
POST /api/v1/auth/register HTTP/1.1
Host: 127.0.0.1:8000
Content-Length: 67
Content-Type: application/json

{"username": "xcx", "email": "xcx@example.com", "password": "123456"}
```

### POST /auth/login

```txt
POST /api/v1/auth/login HTTP/1.1
Host: 127.0.0.1:8000
Content-Length: 40
Content-Type: application/json

{"username": "xcx", "password": "123456"}
```

### GET /auth/me

```txt
GET /api/v1/auth/me HTTP/1.1
Host: 127.0.0.1:8000
Authorization: Bearer eyJhbGciOiJIUz...
```

### GET /user/profile

```txt
GET /api/v1/user/profile HTTP/1.1
Host: 127.0.0.1:8000
Authorization: Bearer eyJhbGciOiJIUz...
```

### PUT /user/profile

```txt
PUT /api/v1/user/profile HTTP/1.1
Host: 127.0.0.1:8000
Authorization: Bearer eyJhbGciOiJIUz...
Content-Type: application/json
Content-Length: 24

{"username": "test_xcx"}
```

### POST /user/avatar

```cmd
curl -X POST "http://127.0.0.1:8000/api/v1/user/avatar" -H "Authorization: Bearer eyJhbGciOiJIUz..." -F "avatar=@C:\Users\...\avatar.png"
```
