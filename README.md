# Agent Security Platform

Agent Security Platform 是一个面向 AI Agent 安全评测的平台仓库，当前包含前端原型、后端基础能力、接口契约文档与设计文档。

## 当前实现状态

- 前端：页面与交互已较完整，覆盖首页、评测目录、评测项详情、智能体提交、评测记录、评测详情、个人资料等页面；数据集浏览、提交评测、评测记录相关能力默认主要基于 mock 数据，并支持切换到真实 API。
- 后端：当前已实现用户认证、用户资料读写、头像上传、统一响应格式、JWT 鉴权、PostgreSQL 连接与 Alembic 迁移基础设施。
- 设计与契约：数据集管理、提交评测、Runner/Oracle、评测报告等更完整的平台能力目前主要体现在 [share/database&submit接口.md](./share/database&submit接口.md) 和 [docs/评测平台后端设计.md](./docs/评测平台后端设计.md) 中，不等同于当前后端已全部实现。

## 项目结构

以下目录树基于当前仓库实际内容整理，省略了 `node_modules`、`dist`、`__pycache__` 等生成物和缓存目录；辅助型 `__init__.py`、聚合型 `index.ts` 和文档图片资源不逐个展开说明。

```text
agent_security_platform/
├── README.md  # 仓库级总览与开发入口
├── backend/
│   ├── .env.example
│   ├── .python-version
│   ├── README.md  # 后端运行、迁移与接口示例说明
│   ├── alembic.ini
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── run.py  # 读取配置并启动开发态 Uvicorn
│   ├── uv.lock
│   ├── alembic/  # 数据库迁移环境与版本脚本
│   │   ├── env.py  # Alembic 迁移环境与 metadata 装配
│   │   ├── script.py.mako  # 新迁移脚本模板
│   │   └── versions/
│   │       └── 6dbccc598a4b_init_user.py  # 初始化 users 表的首个迁移
│   ├── app/  # FastAPI 应用源码
│   │   ├── main.py  # 应用入口、异常处理与 /uploads 静态挂载
│   │   ├── api/  # 路由、依赖与统一响应封装
│   │   │   ├── deps.py  # 数据库会话与当前用户依赖
│   │   │   ├── response.py  # success/fail/401 响应封装
│   │   │   ├── router.py  # /api 根路由入口
│   │   │   └── v1/
│   │   │       ├── api.py  # API v1 路由聚合
│   │   │       └── endpoints/
│   │   │           ├── auth.py  # 登录、注册与当前用户接口
│   │   │           └── user.py  # 个人资料与头像上传接口
│   │   ├── core/  # 配置与安全能力
│   │   │   ├── config.py  # 环境配置与数据库连接 URL
│   │   │   └── security.py  # 密码哈希与 JWT 编解码
│   │   ├── crud/  # 数据访问层
│   │   │   └── user.py  # 用户查询、创建与保存操作
│   │   ├── db/  # SQLAlchemy 基础设施
│   │   │   ├── base.py  # Declarative Base 与命名约定
│   │   │   └── session.py  # 异步引擎与 Session 工厂
│   │   ├── models/  # ORM 模型定义
│   │   │   └── user.py  # users 表 ORM 模型
│   │   └── schemas/  # Pydantic 数据模型
│   │       ├── auth.py  # 登录注册与资料更新 schema
│   │       └── user.py  # 通用用户数据 schema
│   └── uploads/  # 头像等本地上传文件目录
├── docs/
│   ├── 评测平台后端设计.md  # 目标后端架构、领域模型与表设计草案
│   ├── 算法分享.md  # 风险分类、数据集来源与评测思路说明
│   └── 算法分享.assets/  # 文档配图资源
├── frontend/
│   ├── env.d.ts
│   ├── index.html
│   ├── package.json
│   ├── package-lock.json
│   ├── tsconfig.app.json
│   ├── tsconfig.json
│   ├── tsconfig.node.json
│   ├── vite.config.ts
│   └── src/  # 前端业务源码
│       ├── App.vue  # 根组件，承载路由视图与全局登录弹窗
│       ├── main.ts  # 应用启动、Pinia 注册与未授权全局处理
│       ├── api/  # 接口访问、mock/live 切换与数据适配
│       │   ├── AgentService.ts  # 提交流程与评测记录服务
│       │   ├── Config.ts  # mock/live 开关与 API 基础地址配置
│       │   ├── DatasetService.ts  # 评测目录与详情服务
│       │   ├── MockApiUtils.ts  # mock 响应、延迟与失败注入工具
│       │   ├── adapters/
│       │   │   └── DatasetAdapters.ts  # 提交参数与 submit-meta 兼容适配
│       │   └── fixtures/
│       │       └── DatasetFixtures.ts  # 目录、详情、榜单与评测记录 mock 数据
│       ├── components/  # 页面组件与可复用 UI
│       │   ├── common/
│       │   │   ├── FormField.vue  # 通用输入字段组件
│       │   │   └── PageHeroCard.vue  # 页面顶部 Hero 卡片
│       │   ├── dataset/
│       │   │   ├── DatasetCategorySection.vue  # 风险域分区与评测项列表
│       │   │   ├── DatasetFilterBar.vue  # 目录筛选、全选与清空工具栏
│       │   │   ├── DatasetMediaGallery.vue  # 评测项媒体资源展示
│       │   │   └── DatasetSubcategoryCard.vue  # 单个评测项摘要卡片
│       │   ├── dialog/
│       │   │   ├── ConfirmDialog.vue  # 通用确认弹窗
│       │   │   └── LoginDialog.vue  # 登录注册弹窗
│       │   ├── icon/
│       │   │   └── AppIcon.vue  # Iconify 图标统一封装
│       │   ├── navigation/
│       │   │   ├── NavBar.vue  # 顶部导航与用户入口
│       │   │   └── UserSidebar.vue  # 用户中心侧边导航
│       │   └── submit/
│       │       ├── SubmitActionBar.vue  # 提交页状态提示与提交按钮区
│       │       ├── SubmitBasicInfoForm.vue  # 智能体基础信息与接入信息表单
│       │       ├── SubmitDatasetPanel.vue  # 提交页评测项树选择器
│       │       ├── SubmitMethodSelector.vue  # API 与 Docker 提交方式切换
│       │       ├── SubmitParameterControls.vue  # 难度、超时和重试参数控件
│       │       ├── SubmitSection.vue  # 提交页通用分区容器
│       │       └── SubmitVisibilityCard.vue  # 排行榜公开设置开关
│       ├── composables/  # 可复用组合式逻辑
│       │   ├── useDialogBase.ts  # 通用弹窗开关与交互逻辑
│       │   ├── usePersistentStore.ts  # 带本地持久化的通用状态加载器
│       │   └── useSubmitDatasetCatalog.ts  # 提交页按难度加载评测目录
│       ├── constants/  # 常量与参考数据定义
│       │   ├── DatasetTaxonomy.ts  # 参考风险域 taxonomy 与数据集种子
│       │   └── StorageKeys.ts  # localStorage 键名常量
│       ├── layouts/  # 页面骨架布局
│       │   ├── PublicLayout.vue  # 公共页面布局
│       │   └── UserLayout.vue  # 用户页面布局
│       ├── router/  # 路由定义与守卫
│       │   ├── index.ts  # 创建路由实例并注册全局守卫
│       │   ├── RouteGuards.ts  # 登录态拦截与跳转守卫
│       │   ├── RouteMeta.d.ts  # 路由 meta 类型扩展
│       │   ├── RouteNames.ts  # 命名路由与跳转辅助对象
│       │   └── modules/
│       │       ├── LegacyRoutes.ts  # 历史 URL 到新地址的重定向
│       │       ├── PublicRoutes.ts  # 公共页面路由表
│       │       └── UserRoutes.ts  # 登录后用户页面路由表
│       ├── store/  # Pinia 状态管理
│       │   ├── DatasetCatalogStore.ts  # 目录加载、筛选与详情缓存状态
│       │   ├── SubmitDraftStore.ts  # 提交表单草稿持久化与目录同步状态
│       │   └── UserStore.ts  # 登录态、个人资料与头像状态
│       ├── styles/  # 全局样式体系
│       │   ├── LayoutShared.css  # 通用页面布局样式
│       │   ├── Primitives.css  # 基础元素重置与原子样式
│       │   ├── Semantic.css  # 语义化 UI 样式约定
│       │   ├── Tokens.css  # 设计 token 与全局变量
│       │   └── Utilities.css  # 通用工具类样式
│       ├── types/  # 前端类型定义
│       │   ├── AgentTypes.ts  # 提交、评测与表单相关类型
│       │   ├── CommonTypes.ts  # 通用响应与持久化类型
│       │   └── DatasetTypes.ts  # 评测目录与详情数据类型
│       ├── utils/  # 请求、存储与业务工具函数
│       │   ├── Request.ts  # Axios 封装与 401 全局处理
│       │   ├── StorageUtils.ts  # 本地持久化读写与版本控制
│       │   ├── common/
│       │   │   └── DatasetUtils.ts  # 风险域主题、筛选与选择辅助函数
│       │   └── submit/
│       │       └── ParameterValidator.ts  # 提交参数归一化与表单校验
│       └── views/  # 页面级视图
│           ├── ContactUs.vue  # 联系方式与反馈入口页
│           ├── DatasetCatalogPage.vue  # 评测目录浏览页
│           ├── DatasetDetail.vue  # 单个评测项详情页
│           ├── EvaluationReport.vue  # 单次评测详情与指标页
│           ├── HomePage.vue  # 首页与快速入口
│           ├── LeaderboardPage.vue  # 公开排行榜页
│           ├── ProfilePage.vue  # 个人资料与头像修改页
│           ├── SubmitAgentPage.vue  # 智能体提交页
│           └── UserCenter.vue  # 评测记录列表页
└── share/
    ├── database&submit接口.md  # 数据集、提交评测与评测结果接口契约
    ├── git规范.md  # 仓库协作与提交规范
    └── user接口.md  # 认证、资料与头像接口说明
```

## 架构与模块说明

### 前端

前端使用 Vue 3 + TypeScript + Vite + Pinia + Vue Router，当前代码组织更适合按模块理解，而不是把所有未来能力写成“已实现”。

- `src/api/`
  负责 API 访问、mock/live 切换、前端数据适配和 mock fixtures。
- `src/components/`
  负责页面组件和可复用 UI，按 `common`、`dataset`、`dialog`、`navigation`、`submit` 分组。
- `src/composables/` 与 `src/store/`
  负责组合式逻辑、草稿持久化、目录加载、用户状态和页面级状态管理。
- `src/router/`、`src/layouts/`、`src/views/`
  负责页面布局、路由模块拆分、登录守卫和具体页面组合。
- `src/styles/`、`src/constants/`、`src/types/`、`src/utils/`
  负责设计 token、全局样式、常量、类型定义、HTTP 封装及业务工具函数。

当前前端主要面向以下场景：

- 评测目录浏览与评测项详情查看
- 智能体提交表单、参数预检查、草稿持久化
- 用户评测记录和评测详情展示
- 登录弹窗、登录态恢复和未授权回退

### 后端

后端使用 FastAPI + SQLAlchemy + Alembic，当前代码聚焦在“基础能力已落地，平台核心业务仍在继续补齐”的阶段。

- `app/main.py`
  应用入口，挂载 `/uploads` 静态目录并注册全局异常处理与 API 路由。
- `app/api/`
  负责路由编排、依赖注入、统一响应封装和 API v1 入口。
- `app/api/v1/endpoints/`
  当前仅包含 `auth.py` 与 `user.py`，即认证与用户信息相关接口。
- `app/core/`
  负责环境配置、密码哈希、JWT 等安全相关逻辑。
- `app/db/`、`app/models/`、`app/crud/`、`app/schemas/`
  负责数据库会话、ORM 模型、数据访问和 Pydantic schema。
- `alembic/`
  负责数据库迁移。
- `uploads/`
  负责头像等上传文件的本地存储。

## 前端运行模式

前端通过环境变量在 mock 数据与真实后端之间切换：

- `VITE_USE_LIVE_REFERENCE_API`
  控制数据集目录、数据集详情、提交元数据等“参考数据类”接口是否走真实后端。
- `VITE_USE_LIVE_SUBMISSION_API`
  控制提交流程、评测记录、评测详情等“提交与结果类”接口是否走真实后端。
- `VITE_API_BASE_URL`
  控制前端请求的 API 基础地址；`frontend/src/utils/Request.ts` 中默认值为 `/api/v1`。

建议使用方式：

- 页面开发阶段：两个 `VITE_USE_LIVE_*` 默认设为 `false`，优先使用前端 mock 数据。
- 联调阶段：按需逐步切换到真实接口。
- 若前后端同域部署，`VITE_API_BASE_URL=/api/v1` 即可；本地跨端口联调时可改为例如 `http://localhost:8000/api/v1`。

## 后端当前接口范围

当前后端代码中已经存在并可对齐到实现的接口主要是用户与认证相关接口：

- `POST /api/v1/auth/login`
- `POST /api/v1/auth/register`
- `GET /api/v1/auth/me`
- `GET /api/v1/user/profile`
- `PUT /api/v1/user/profile`
- `POST /api/v1/user/avatar`

当前统一响应格式为：

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

需要特别区分：

- [share/user接口.md](./share/user接口.md) 主要对应当前已实现的认证与用户接口。
- [share/database&submit接口.md](./share/database&submit接口.md) 主要描述前后端对“数据集、提交评测、评测记录”等能力的接口契约。
- [docs/评测平台后端设计.md](./docs/评测平台后端设计.md) 主要描述目标后端架构与演进方向。

后两者不应被理解为“当前后端已全部具备这些接口和能力”。

## 启动与开发

### 前端

前置条件：

- Node.js 版本满足 `^20.19.0 || >=22.12.0`
- npm 可用

常用命令：

```bash
cd frontend
npm install
npm run dev
```

类型检查：

```bash
cd frontend
npm run type-check
```

生产构建：

```bash
cd frontend
npm run build
```

说明：

- `npm run build` 会先执行 `npm run type-check`，再执行 `npm run build-only`。
- 构建产物输出到 `frontend/dist/`，该目录属于构建结果，不作为仓库结构说明的一部分。

### 后端

前置条件：

- Python 3.12+
- PostgreSQL
- 已按需准备 `backend/.env`

先复制环境变量模板：

```powershell
cd backend
Copy-Item .env.example .env
```

如果使用 `pip`：

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
python run.py
```

如果使用 `uv`：

```bash
cd backend
uv sync
uv run alembic upgrade head
uv run python run.py
```

补充说明：

- `backend/.env.example` 中定义了 `PROJECT_NAME`、`FASTAPI_HOST`、`FASTAPI_PORT`、PostgreSQL 连接参数等基础配置。
- `python run.py` 会从配置中读取主机和端口，并以开发模式启动 Uvicorn。
- 上传文件默认存放在 `backend/uploads/`，并通过 FastAPI 挂载到 `/uploads` 路径。
- 更详细的后端运行和迁移说明可见 [backend/README.md](./backend/README.md)。

## 文档与约定

### 后端实现与运行

- [backend/README.md](./backend/README.md)：后端项目的详细运行说明、迁移命令和接口示例，侧重当前后端实现。

### 后端设计

- [docs/评测平台后端设计.md](./docs/评测平台后端设计.md)：平台后端的目标架构、领域模型、表设计与演进建议，属于设计稿，不代表全部已落地。

### 前后端接口契约

- [share/user接口.md](./share/user接口.md)：认证、用户资料、头像上传等接口说明，最接近当前已实现的后端能力。
- [share/database&submit接口.md](./share/database&submit接口.md)：数据集目录、提交评测、评测记录与评测详情等接口契约，主要用于前后端联调与后续实现。

### 风险分类与数据集背景

- [docs/算法分享.md](./docs/算法分享.md)：风险分类体系、数据集来源、任务定义样例与评测思路说明。

### Git 规范

- [share/git规范.md](./share/git规范.md)：仓库协作时的提交与分支约定。

## 说明

- 根 `README.md` 只做仓库级总览，不重复展开所有后端细节。
- 看到设计文档或接口契约时，请优先结合“当前实现状态”和实际代码判断哪些能力已经落地。
- 本仓库当前更适合被理解为“平台原型 + 后端基础设施 + 契约/设计文档”的组合，而不是功能完全闭环的成品系统。
