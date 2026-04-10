# Agent Security Platform

## 项目概览

当前仓库包含三个核心部分：

- `frontend/`：Vue 3 + TypeScript 前端
- `backend/`：FastAPI 后端
- `share/`：前后端共享接口文档

本轮前端已完成目录重构、基础脚手架刷新，以及面向用户页面的移动端适配优化。

## 前端目录约定

前端源码以 `frontend/src` 为根，按职责拆分为四层：

- `app/`：应用装配层，包含路由、布局、Shell 和全局样式
- `modules/`：业务模块，按 `public / dataset / submission / evaluation / account` 聚合
- `shared/`：跨模块复用的 UI、类型、通用能力与静态资源
- `shared/api/core/HttpClient.ts`：统一 HTTP 请求入口

## 品牌资源约定

- 浏览器页签图标固定使用 `frontend/public/favicon.svg`
- 页面展示用 Logo 统一放在 `frontend/src/shared/assets/branding/logo.svg`
- 页面中使用 Logo 时，通过源码导入接入，不再依赖 `public/` 固定路径

## 首页与导航行为

- 首页标题“智能体安全评测平台”和副标题“安全 · 可靠 · 专业的智能体评估系统”采用首次进入的较慢打字机动画
- 若浏览器设置了 `prefers-reduced-motion: reduce`，首页会直接展示完整文案
- 评测目录默认展示后端返回的首个启用风险域，页面始终只展示一个风险域的评测项，点击风险域标签可切换查看
- 登录后顶部导航新增“评测记录”和“提交测评”入口，头像区作为唯一个人资料入口
- 登录后除首页外的页面在桌面端统一显示左侧导航栏；移动端继续由顶部抽屉菜单承接导航
- 评测任务详情页在非终态下每 10 分钟自动轮询一次详情；首次进入、路由切换和任务动作后仍立即刷新
- 移动端主导航统一采用抽屉菜单
- 登录后页面的左侧边栏仅在桌面端显示；移动端由顶部抽屉统一承接用户导航

## 移动端适配范围

当前已覆盖全部用户可访问页面：

- 首页
- 评测目录
- 评测详情
- 排行榜
- 联系我们
- 404 页面
- 评测记录
- 评测任务详情
- 提交智能体
- 个人资料

适配目标包括：

- 避免横向滚动
- 统一缩小移动端边距、卡片内边距和标题层级
- 把高密度表格或双栏内容收敛为窄屏优先的纵向布局

## 前端运行模式

前端默认以真实后端为准，不再使用旧的环境变量：

- `VITE_USE_LIVE_REFERENCE_API`
- `VITE_USE_LIVE_SUBMISSION_API`

当前有效环境变量为：

- `VITE_API_BASE_URL`
- `VITE_BACKEND_TARGET`
- `VITE_ENABLE_API_MOCK`
- `VITE_ENABLE_LEADERBOARD_MOCK`

### 同源代理联调

适合本地前后端同时启动：

```env
VITE_API_BASE_URL=/api/v1
VITE_BACKEND_TARGET=http://127.0.0.1:8001
VITE_ENABLE_API_MOCK=false
VITE_ENABLE_LEADERBOARD_MOCK=false
```

### 直连真实后端

适合前端直接访问完整后端地址：

```env
VITE_API_BASE_URL=http://127.0.0.1:8001/api/v1
VITE_ENABLE_API_MOCK=false
VITE_ENABLE_LEADERBOARD_MOCK=false
```

### 显式业务 Mock

仅影响已接入 Mock 的提交与评测链路：

```env
VITE_ENABLE_API_MOCK=true
VITE_ENABLE_LEADERBOARD_MOCK=false
```

### 排行榜 Mock

排行榜功能尚未接入正式接口；若需演示可单独开启：

```env
VITE_ENABLE_LEADERBOARD_MOCK=true
```

## 前端缓存与持久化边界

### 页面生命周期内缓存

当前仅对以下 GET 资源启用内存缓存：

- `GET /api/v1/datasets/catalog`
- `GET /api/v1/datasets/{datasetId}`
- `GET /api/v1/agents/submit-meta`

### localStorage 持久化范围

当前仅允许持久化：

- token
- 登录后回跳地址
- 提交草稿
- 纯 UI 状态

在真实 API 模式下，以下内容不作为 durable localStorage 真相源：

- 评测记录
- 评测详情
- precheck 结果
- submit 结果

## 常用命令

```bash
cd frontend
npm install
npm run type-check
npm run build
npm run dev
```

## 相关文档

- 前端本地快速说明：`frontend/README.md`
- [share/database&submit接口.md](./share/database&submit接口.md)
- [share/evaluations接口.md](./share/evaluations接口.md)
- [share/user接口.md](./share/user接口.md)
- [share/API接口协议.md](./share/API接口协议.md)

## 文本编码约定

仓库内本轮修改的受控文本文件统一约定为：

- UTF-8 无 BOM
- CRLF 行尾
