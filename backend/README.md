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
