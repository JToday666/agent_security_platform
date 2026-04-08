# Backend README

## 1. 项目定位

本目录是评测平台后端服务，基于 FastAPI + SQLAlchemy + PostgreSQL，当前包含用户认证与用户资料相关接口。

## 2. 后端结构（重点）

```text
backend/
├── app/
│   ├── main.py                    # FastAPI 入口，静态资源挂载，异常处理注册
│   ├── api/
│   │   ├── response.py            # 统一响应封装：success/fail/unauthorized
│   │   ├── deps.py                # DB Session 与当前用户依赖
│   │   ├── router.py              # /api 路由聚合
│   │   └── v1/
│   │       ├── api.py             # /api/v1 路由聚合
│   │       └── endpoints/
│   │           ├── auth.py        # 登录/注册/当前用户
│   │           └── user.py        # 资料读取/更新/头像上传
│   ├── core/
│   │   ├── config.py              # 环境变量与数据库 URL 构建
│   │   └── security.py            # 密码哈希与 JWT
│   ├── crud/                      # 数据访问层
│   ├── db/
│   │   ├── base.py                # SQLAlchemy Base 与命名约定
│   │   └── session.py             # 异步引擎与 AsyncSession
│   ├── models/                    # ORM 模型
│   └── schemas/                   # Pydantic 模型
├── alembic/                       # 数据库迁移目录
├── alembic.ini
├── pyproject.toml
├── requirements.txt
└── run.py
```

## 3. 技术栈与关键约定

- 框架：FastAPI
- 数据层：SQLAlchemy 2.x（async session）
- 驱动：
  - 运行时：asyncpg（`postgresql+asyncpg`）
  - Alembic 迁移：psycopg（`postgresql+psycopg`）
- 鉴权：JWT（PyJWT）+ HTTP Bearer
- 密码：PBKDF2-SHA256（100000 迭代）
- 统一响应：`{ code, data, message }`

## 4. 环境变量

先复制并修改：

```powershell
Copy-Item .env.example .env
```

核心变量：

- `FASTAPI_HOST`（默认 `127.0.0.1`）
- `FASTAPI_PORT`（默认 `8000`）
- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `SECRET_KEY`
- `JWT_ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_MINUTES`

## 5. 运行方式

以下命令都在 `backend/` 目录执行。

### 5.1 使用 uv（推荐）

```bash
uv sync
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

或：

```bash
uv run python run.py
```

### 5.2 使用 pip

```bash
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## 6. 数据库与迁移

### 6.1 迁移原则

- 所有 Schema 变更必须通过 Alembic。
- 应用代码不应调用 `create_all` 做自动建表。
- 新增模型后，需要在 `app/models/__init__.py` 导入，确保 `--autogenerate` 可发现。

### 6.2 常用命令

```bash
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "your message"
uv run alembic downgrade -1
uv run alembic current
uv run alembic history
```

如不使用 `uv`，可替换为：

```bash
python -m alembic upgrade head
```

### 6.3 Alembic 规范（新增）

- 所有 schema 变更必须通过迁移交付，不在运行时代码中执行自动建表。
- 生成迁移前先确认模型已在 `app/models/__init__.py` 导入，避免漏检。
- 迁移 message 采用“动作 + 对象”命名，避免 `update`、`fix` 这类无语义名称。
- 使用 `--autogenerate` 后必须人工审核迁移脚本，重点关注：
  - 非预期 `drop_table` / `drop_column` / `drop_index`
  - 非预期约束与索引变化
  - 类型变更是否对现有数据兼容
- 破坏性变更（删字段、重命名、不兼容类型）需要在变更说明中写清：
  - 影响范围
  - 兼容策略
  - 回滚方案

推荐提交流程：

```bash
uv run alembic upgrade head
uv run alembic current
# 可选：验证回滚链路
uv run alembic downgrade -1
uv run alembic upgrade head
```

## 7. API 与响应格式

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
