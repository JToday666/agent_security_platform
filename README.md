# Agent Security Platform

## 项目结构

- `frontend/`: Vue 3 + TypeScript 前端。
- `backend/`: FastAPI 后端。
- `share/`: 当前前后端接口约定文档。

## 当前前端约定

前端源码根目录为 `frontend/src`，主要分为三层：

- `app/`: 路由、布局、Shell 与全局装配。
- `modules/`: 业务模块，按 `public / dataset / submission / evaluation / account` 划分。
- `shared/`: 跨模块共享的 UI、类型、通用 API 能力与工具函数。

### `shared/ui` 目录

本轮已按职责拆分为以下子目录：

- `shared/ui/actions/`: 按钮等交互动作组件。
- `shared/ui/branding/`: 品牌 Logo、图标等品牌元素。
- `shared/ui/display/`: 标签、指标卡、状态标签等展示组件。
- `shared/ui/feedback/`: 弹窗、提示条、页面状态卡等反馈组件。
- `shared/ui/forms/`: 表单字段、切换卡、选项卡等表单组件。
- `shared/ui/page/`: Hero、Section 等页面级公共外壳。

拆分目的：

- 降低 `shared/ui` 平铺文件过多带来的查找成本。
- 让通用外壳、表单、反馈、展示组件边界更清晰。
- 在不改变页面视觉的前提下，减少后续扩展时的目录混乱。

### `shared/api` 目录

前端共享 API 工具已从原先的 `shared/api/core` 平铺到 `shared/api`：

- `Config.ts`
- `HttpClient.ts`
- `ApiRuntime.ts`
- `MemoryCache.ts`
- `MockApiUtils.ts`

当前目录规模下，直接平铺比仅保留一个 `core` 子目录更简洁，减少了一层无实际收益的路径嵌套。

## 当前页面补充

### 数据集详情页

- “准备发起评测”区块中的标题、说明与按钮为居中排布。
- 该区块用于承接从数据集详情直接进入提交页的入口。

### 评测报告详情页

- 顶部摘要区仅保留状态文字和图标标记，不再在彩色标记中重复展示相同文案。
- 数据集数量卡片仅展示数量，不再展示具体数据集名称列表。

### 提交评测页

- API Token 文案已改为面向用户的说明，不再使用开发者导向描述。
- 目录刷新后若移除了失效数据集或展开状态，页面不再显示黄色提示，内部仅静默同步状态。
- 提交页草稿仍只保留在当前页面会话内，不写入 durable localStorage。

### 联系我们页

- Hero 区中 logo、标题与长文案均为居中布局，分别独占一行。

## 前端运行

```bash
cd frontend
npm install
npm run dev
npm run test
npm run type-check
npm run build
```

## 环境变量

前端当前只使用以下环境变量：

- `VITE_API_BASE_URL`
- `VITE_BACKEND_TARGET`
- `VITE_ENABLE_API_MOCK`

说明：

- `VITE_API_BASE_URL` 控制前端请求基地址。
- `VITE_BACKEND_TARGET` 只用于 Vite 本地代理目标，不属于前端运行时业务配置。
- `VITE_ENABLE_API_MOCK=true` 时，数据集、提交、评测相关链路统一走前端 mock 实现。

推荐本地联调配置：

```env
VITE_API_BASE_URL=/api/v1
VITE_BACKEND_TARGET=http://127.0.0.1:8001
VITE_ENABLE_API_MOCK=false
```

直接访问后端：

```env
VITE_API_BASE_URL=http://127.0.0.1:8001/api/v1
VITE_ENABLE_API_MOCK=false
```

显式启用前端 mock：

```env
VITE_ENABLE_API_MOCK=true
```

## 测试

前端测试已迁移到 Vitest：

- `npm run test`: 运行 `src/**/*.vitest.ts`
- `npm run type-check`: 运行 `vue-tsc -b`

组件测试链路已不再依赖旧的重复测试文件结构，目录与依赖均已按当前工程状态收口。

## 缓存与持久化边界

### 内存缓存

当前前端只对以下读取接口做内存缓存：

- `GET /datasets/catalog`
- `GET /datasets/{datasetId}`
- `GET /agents/submit-meta`

其中：

- 数据集目录页和提交页都支持 `force` 刷新，能够绕过内存缓存重新请求。
- 评测记录与评测详情不做 durable 本地缓存，详情页仅按页面逻辑轮询或动作后刷新。

### localStorage

当前允许写入 localStorage 的内容只有：

- 用户 token
- 登录后跳转地址
- 会话级滚动位置
- mock 评测记录（仅 mock 链路）

提交页草稿不再写入 localStorage，只在当前页面会话内保留。

## 文档

- [share/database&submit接口.md](./share/database&submit接口.md)
- [share/evaluations接口.md](./share/evaluations接口.md)
- [share/user接口.md](./share/user接口.md)
- [share/API接口协议.md](./share/API接口协议.md)

## 文本编码

本轮修改后的文本文件统一为：

- UTF-8 无 BOM
- CRLF 行尾
