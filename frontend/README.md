# Frontend README

## 1. 项目定位

`frontend/` 是 Agent Security Platform 的前端工程，基于 Vite + Vue 3 + TypeScript + Pinia + Vue Router。

当前前端覆盖以下能力：

- 公共页面：首页、数据集目录、数据集详情、排行榜、联系页、404
- 账号能力：登录、注册、登录态恢复、个人资料与头像上传
- 数据集能力：目录加载、详情加载、分类筛选、排序、详情跳转提交页
- 评测能力：提交前预检查、正式提交、记录列表、详情查看、任务动作
- 运行模式：真实后端 API 与 Mock API 双模式切换

源码按三层组织：

- `src/app/`：应用壳层，负责启动、路由、布局、导航、全局样式
- `src/modules/`：业务模块层，按 `account / dataset / evaluation / public / submission` 分域
- `src/shared/`：共享基础设施，收口 API 基础封装、类型、工具与共享 UI

README 只写前端当前状态、运行方式、命名规范和文档入口。更细的内部说明在 `frontend/docs/`，跨端接口契约主维护在 `share/`。

## 2. 当前核心目录

- `src/app/`：布局、路由、导航外壳、SCSS 设计体系
- `src/modules/`：业务模块代码
- `src/shared/`：共享 API、类型、工具、UI
- `public/`：不经构建处理的静态资源
- `vite.config.ts`：Vite 配置、`@` 别名与开发代理
- `.env.example`：环境变量模板

## 3. 快速开始

以下命令都在 `frontend/` 目录执行。

安装依赖：

```bash
npm install
```

启动开发环境：

```bash
npm run dev
```

构建生产包：

```bash
npm run build
```

本地预览构建结果：

```bash
npm run preview
```

仅做类型检查：

```bash
npm run type-check
```

## 4. 运行约束

Node 版本要求来自 `package.json`：

- `>=24.14.1 <25`

环境变量以 `.env.example` 为准：

- `VITE_API_BASE_URL`
  前端请求 API 时使用的基础路径，默认可配置为 `/api/v1`
- `VITE_BACKEND_TARGET`
  Vite 开发代理的目标后端地址，`vite.config.ts` 会把 `/api`、`/uploads` 转发到这里
- `VITE_ENABLE_API_MOCK`
  是否启用前端本地 Mock 实现；为 `true` 时，数据集与评测能力会优先走 Mock 分支

运行建议：

- 本地联调真实后端时，通常保持 `VITE_ENABLE_API_MOCK=false`
- 想脱离后端独立演示评测链路时，可切到 `VITE_ENABLE_API_MOCK=true`
- 若修改 API 基础路径或代理目标，优先同时检查 `src/shared/api/config.ts` 和 `vite.config.ts`

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

旧的页面级共享组件命名已全部收口，不再作为当前前端基线。

## 6. 检查与验证

文档任务之外的日常开发，最常用的最小验证组合如下：

类型检查：

```bash
npm run type-check
```

构建检查：

```bash
npm run build
```

说明：

- `npm run build` 实际会先执行 `type-check`，再执行 `build-only`
- 当前仓内不保留 `frontend/src` 下测试源码；日常验证以类型检查、构建和定向页面走查为主

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
- [账号与鉴权模块说明](./docs/03-模块/账号与鉴权模块说明.md)
- [数据集模块说明](./docs/03-模块/数据集模块说明.md)
- [提交评测模块说明](./docs/03-模块/提交评测模块说明.md)
- [评测模块说明](./docs/03-模块/评测模块说明.md)
- [公共页面与共享 UI 说明](./docs/03-模块/公共页面与共享UI说明.md)
- [关键链路说明](./docs/04-流程/关键链路说明.md)
- [文档维护约定](./docs/05-规范/文档维护约定.md)

跨端接口契约：

- [API 接口协议总表](../share/API接口协议.md)
- [用户接口补充说明](../share/user接口.md)
- [数据集与提交接口补充说明](../share/database&submit接口.md)
- [评测记录与报告接口补充说明](../share/evaluations接口.md)

推荐阅读顺序：

1. 先看本 README，确认运行方式和分层
2. 再看 [文档地图](./docs/01-总览/文档地图.md) 和 [前端架构说明](./docs/01-总览/前端架构说明.md)
3. 需要改具体业务时，进入对应模块文档
4. 需要追调用链时，看 [关键链路说明](./docs/04-流程/关键链路说明.md)
5. 需要核对字段语义或请求契约时，看 `share/` 下接口文档

## 9. 文档边界

- `frontend/README.md`：前端入口，只写当前状态、运行命令、命名规范、文档索引
- `frontend/docs/`：前端内部结构、模块与流程说明
- `share/`：跨端接口契约主文档

同一个事实只保留一个主维护位置：

- 接口字段、接口路径、请求响应契约，以 `share/` 为准
- 前端分层、页面职责、状态流转、共享 UI 使用边界，以 `frontend/docs/` 为准
