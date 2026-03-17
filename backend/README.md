# README

## 架构说明

### 项目结构

```markdown
backend/
├── app/
│   ├── main.py              # 应用入口
│   ├── api/
│   │   ├── router.py        # 路由配置
│   │   ├── deps.py          # 依赖注入
│   │   └── v1/
│   │       ├── api.py       # API版本管理
│   │       └── endpoints/   # 具体端点实现
│   ├── core/
│   │   └── config.py        # 配置管理
│   ├── crud/                # 数据库操作层
│   ├── db/
│   │   ├── base.py          # 数据库基础配置
│   │   └── session.py       # 数据库会话
│   ├── models/              # 数据库模型
│   └── schemas/             # Pydantic数据模型
├── requirements.txt         # 项目依赖
├── run.py                   # 启动脚本
├── .env                     # 环境变量配置
└── README.md                # 项目说明
```

### 技术栈

- **框架**：FastAPI
- **服务器**：Uvicorn
- **数据验证**：Pydantic

## 后端运行方法

### 包方式启动

在backend目录下运行

```shell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

注意

- 端口号可能有冲突，可以调整
- host默认127.0.0.1
- --reload适合开发环境，生产环境不要开启

### 运行run

直接运行

### IDE配置

vscode/pycharm

## 后端测试

### POST /auth/register

```txt
POST /api/v1/auth/register HTTP/1.1
Host: 127.0.0.1:8002
Content-Length: 67
Content-Type:application/json

{"username": "xcx","email": "xcx@example.com","password": "123456"}
```

### POST /auth/login

```txt
POST /api/v1/auth/login HTTP/1.1
Host: 127.0.0.1:8002
Content-Length: 40
Content-Type:application/json

{"username": "xcx","password": "123456"}
```

### GET /auth/me

```txt
GET /api/v1/auth/me HTTP/1.1
Host: 127.0.0.1:8002
Authorization: Bearer eyJhbGciOiJIUz...


```

### GET /user/profile

```txt
GET /api/v1/user/profile HTTP/1.1
Host: 127.0.0.1:8002
Authorization: Bearer eyJhbGciOiJIUz...


```

### PUT /user/profile

```txt
PUT /api/v1/user/profile HTTP/1.1
Host: 127.0.0.1:8002
Authorization: Bearer eyJhbGciOiJIUz...
Content-Type:application/json
Content-Length: 24

{"username": "test_xcx"}
```

### POST /user/avatar

```cmd
curl -X POST "http://127.0.0.1:8002/api/v1/user/avatar" -H "Authorization: Bearer eyJhbGciOiJIUz..." -F "avatar=@C:\Users\...\avatar.png"
```
