# Frontend README

## 1. 项目定位

`frontend/` 是 Agent Security Platform 的前端工程，基于 Vite + Vue + TypeScript + Pinia + Vue Router，并预留 `vue-i18n` 国际化资源骨架。

当前前端覆盖以下能力：

- 公共页面：首页、数据集目录、数据集详情、排行榜、联系页、404
- 账号能力：登录、注册、登录态恢复、个人资料与头像上传
- 数据集能力：目录加载、详情加载、分类筛选、排序、详情跳转提交页
- 智能体能力：Agent 管理、注册、详情、验证、归档、复制新建
- 评测能力：提交前预检查、正式提交、历史列表、趋势分析、详情报告阅读流、ECharts 图表、代表样本证据、任务动作
- 排行榜能力：读取 `/leaderboards/current`，展示当前第一名，支持综合分、安全能力、高难分和风险分排序
- 运行模式：真实后端 API 与 Mock API 双模式切换

源码按三层组织：

- `src/app/`：应用壳层，负责启动、路由、布局、导航、国际化入口、全局样式
- `src/modules/`：业务模块层，按 `account / agent / dataset / evaluation / leaderboard / public / submission` 分域
- `src/shared/`：共享基础设施，收口 API 基础封装、类型、工具与共享 UI

更细的内部说明在 `frontend/docs/`，跨端接口契约主维护在 `share/`。

## 2. 当前核心目录

- `src/app/`：布局、路由、导航外壳、移动导航抽屉、国际化资源骨架、SCSS 设计体系
- `src/modules/`：业务模块代码，页面容器、状态组合、展示组件和视图派生按模块放置
- `src/shared/`：共享 API、类型、工具、UI
- `public/`：不经构建处理的静态资源
- `vite.config.ts`：Vite 配置、`@` 别名与开发代理
- `.env.example`：环境变量模板

## 3. 快速开始

以下命令都在 `frontend/` 目录执行。

安装依赖：

```bash
pnpm install --frozen-lockfile
```

启动开发环境：

```bash
pnpm dev
```

构建生产包：

```bash
pnpm build
```

`pnpm build` 会依次执行类型检查和生产构建。常规安装使用 `pnpm install --frozen-lockfile`，需要更新依赖声明或锁文件时再由维护者执行非冻结安装。

本地预览构建结果：

```bash
pnpm preview
```

仅做类型检查：

```bash
pnpm type-check
```

## 4. 运行约束

Node 与包管理器要求以 `package.json` 为准。

环境变量以 `.env.example` 为准：

- `VITE_API_BASE_URL`
  前端请求 API 时使用的基础路径，默认可配置为 `/api/v1`
- `VITE_BACKEND_TARGET`
  Vite 开发代理的目标后端地址，`vite.config.ts` 会把 `/api`、`/uploads` 转发到这里
- `VITE_ENABLE_API_MOCK`
  是否启用前端本地 Mock 实现；为 `true` 时，数据集、Agent、提交与评测能力会优先走 Mock 分支

运行建议：

- 本地联调真实后端时，通常保持 `VITE_ENABLE_API_MOCK=false`
- 想脱离后端独立演示数据集、Agent 注册提交、评测历史、趋势分析和报告阅读流时，可切到 `VITE_ENABLE_API_MOCK=true`
- 若修改 API 基础路径或代理目标，优先同时检查 `src/shared/api/Config.ts` 和 `vite.config.ts`

## 5. 当前共享 UI 基线

页面级共享 UI 目前统一收口为以下组件：

- `src/shared/ui/page/PageHero.vue`
  平铺页面头部容器，负责标题、说明、前缀区、动作区与对齐方式
- `src/shared/ui/page/SectionBlock.vue`
  内容分区容器，支持 `surface="line" | "panel"`
- `src/shared/ui/feedback/PageStatePanel.vue`
  页面级加载、空态、失败态容器
- `src/shared/ui/display/MetricStat.vue`
  指标摘要卡
- `src/shared/ui/forms/UiSelect.vue`
  统一下拉组件，供 `FormField` 的 `type="select"` 模式内部使用
- `src/shared/ui/branding/AppIcon.vue`
  基于 `lucide-vue-next` 的统一图标入口，按语义维护项目内可用图标
- `src/shared/ui/branding/BrandLogo.vue`
  品牌 Logo 组件，使用构建可控的轻量矢量 Logo

> **UI 基线提示**: 平台在共享层引入了现代微交互与玻璃态视觉体系。新组件开发应优先复用 `tokens.scss` 中的高级缓动函数（如 `var(--ease-spring)`）、内发光变量（如 `var(--glass-border-inset)`）及标准的 Hover 反馈，详见 [前端UI设计规范](./docs/05-规范/前端UI设计规范.md)。

模块专用展示组件保留在各自业务模块内，跨模块复用组件放入 `src/shared/ui/`。

## 6. 检查与验证

文档任务之外的日常开发，最常用的最小验证组合如下：

单元测试：

```bash
pnpm test
```

类型检查：

```bash
pnpm type-check
```

构建检查：

```bash
pnpm build
```

说明：

- `pnpm build` 会先执行 `type-check`，再执行 `build-only`
- `pnpm build-only` 只生成生产包，不执行类型检查
- 排行榜、评测图表、报告阅读流、提交表单和页面响应式布局适合结合测试、类型检查、构建和定向页面走查验证

## 7. 前端命名规范

以下规范作为新增文件、重命名文件时的统一标准。

| 文件类型 / 目录                          | 命名风格     | 示例                 |
| ---------------------------------------- | ------------ | -------------------- |
| 普通 `.ts` / `.js` 文件                  | `kebab-case` | `user-service.ts`    |
| 类型声明 `.d.ts`                         | `kebab-case` | `api-types.d.ts`     |
| Vue 组件（`components / views / pages`） | `PascalCase` | `UserProfile.vue`    |
| Composables                              | `camelCase`  | `useAuth.ts`         |
| Pinia store 模块                         | `camelCase`  | `userStore.ts`       |
| 路由文件                                 | `kebab-case` | `dataset-routes.ts`  |
| API 文件                                 | `kebab-case` | `leaderboard-api.ts` |
| 工具函数                                 | `kebab-case` | `format-date.ts`     |
| 自定义指令                               | `kebab-case` | `v-permission.ts`    |
| 文件夹（普通）                           | `kebab-case` | `user-profile/`      |
| 组件文件夹                               | `PascalCase` | `UserAvatar/`        |
| 视图文件夹                               | `PascalCase` | `EvaluationDetail/`  |

阅读和维护当前代码时，以仓库中的真实文件名为准。

## 8. 文档索引与阅读顺序

前端内部文档：

- [文档地图](./docs/01-总览/文档地图.md)
- [前端架构说明](./docs/01-总览/前端架构说明.md)
- [应用启动与运行时说明](./docs/02-架构/应用启动与运行时说明.md)
- [路由布局与导航说明](./docs/02-架构/路由布局与导航说明.md)
- [国际化架构说明](./docs/02-架构/国际化架构说明.md)
- [账号与鉴权模块说明](./docs/03-模块/账号与鉴权模块说明.md)
- [数据集模块说明](./docs/03-模块/数据集模块说明.md)
- [智能体模块说明](./docs/03-模块/智能体模块说明.md)
- [提交评测模块说明](./docs/03-模块/提交评测模块说明.md)
- [评测模块说明](./docs/03-模块/评测模块说明.md)
- [公共页面与共享 UI 说明](./docs/03-模块/公共页面与共享UI说明.md)
- [关键链路说明](./docs/04-流程/关键链路说明.md)
- [前端 UI 设计规范](./docs/05-规范/前端UI设计规范.md)
- [文档维护约定](./docs/05-规范/文档维护约定.md)

跨端接口契约：

- [API 接口协议总表](../share/API接口协议.md)
- [国际化工程指导方案](../share/i18n方案.md)
- [用户接口补充说明](../share/user接口.md)
- [数据集接口补充说明](../share/database接口.md)
- [提交接口补充说明](../share/submit接口.md)
- [Agent 接口补充说明](../share/agent接口.md)
- [报告接口补充说明](../share/report接口.md)
- [排行榜接口补充说明](../share/leaderboard接口.md)

推荐阅读顺序：

1. 先看本 README，确认运行方式和分层
2. 再看 [文档地图](./docs/01-总览/文档地图.md) 和 [前端架构说明](./docs/01-总览/前端架构说明.md)
3. 需要改具体业务时，进入对应模块文档
4. 需要追调用链时，看 [关键链路说明](./docs/04-流程/关键链路说明.md)
5. 需要理解国际化边界时，看 [国际化工程指导方案](../share/i18n方案.md) 和 [国际化架构说明](./docs/02-架构/国际化架构说明.md)
6. 需要核对字段语义或请求契约时，看 `share/` 下接口文档

## 9. 文档边界

- `frontend/README.md`：前端入口，只写当前状态、运行命令、命名规范、文档索引
- `frontend/docs/`：前端内部结构、模块与流程说明
- `share/`：跨端接口契约与国际化总策略主文档

同一个事实只保留一个主维护位置：

- 接口字段、接口路径、请求响应契约和国际化总策略，以 `share/` 为准
- 前端分层、页面职责、状态流转、共享 UI 使用边界，以 `frontend/docs/` 为准
