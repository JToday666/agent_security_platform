# Agent Security Platform

Agent Security Platform 是一个面向 AI Agent 安全评测的仓库，当前同时承载三类内容：

- `frontend/`：Vue 3 + TypeScript 前端原型与联调实现
- `backend/`：FastAPI 后端基础设施与已落地的用户认证能力
- `share/`：当前前端真实依赖的共享接口契约文档

## 当前实现状态

- 前端已经实现数据集目录、数据集详情、智能体提交、评测记录、评测详情和任务控制等页面。
- 数据集目录与评测页面默认隐藏内部 `datasetId`，界面展示统一使用公开名称。
- 提交流程默认可基于 mock 数据闭环运行，也支持按环境变量切换到真实 API。
- 后端代码仓当前已落地的是认证与用户资料相关接口；`datasets / agents / evaluations` 仍以 `share/` 中的契约文档为准，不能视为 `backend/` 已全部实现。

## 关键前端约定

- `GET /api/v1/datasets/catalog` 不再接收 `difficulty` 参数。
- 提交页进入 `/user/submit` 时只请求一次 catalog；后续调整 `difficulty` 不再刷新目录。
- `difficulty` 仍然保留在 `POST /api/v1/agents/precheck` 与 `POST /api/v1/agents/submit` 的 `parameters` 中。
- 前端内部表单字段仍叫 `selectedDatasetIds`，发给后端前统一适配为 `datasetIds`。
- 评测记录和评测详情页面只展示 `datasetNames`、`runningDatasetName`、`statusText` 这类公开文本，不直接显示内部数据集代码。

## 共享文档入口

- [database&submit接口.md](./share/database&submit接口.md)：数据集目录、数据集详情、提交元数据、预检查与正式提交契约
- [evaluations接口.md](./share/evaluations接口.md)：评测记录列表、评测详情快照与任务控制契约
- [user接口.md](./share/user接口.md)：认证、用户资料与头像上传接口
- [git规范.md](./share/git规范.md)：仓库协作与提交规范

## 前端运行模式

前端通过环境变量在 mock 与 live API 之间切换：

- `VITE_USE_LIVE_REFERENCE_API`：控制数据集目录、数据集详情、提交元数据等参考类接口是否走真实后端
- `VITE_USE_LIVE_SUBMISSION_API`：控制提交、评测记录、评测详情与任务控制等流程类接口是否走真实后端
- `VITE_API_BASE_URL`：前端 API 基础地址，默认使用 `/api/v1`

推荐使用方式：

- 页面开发阶段：两个 `VITE_USE_LIVE_*` 变量保持 `false`
- 前后端联调阶段：按需逐步切换到真实接口
- 同域部署：`VITE_API_BASE_URL=/api/v1`
- 本地跨端口联调：例如 `VITE_API_BASE_URL=http://localhost:8000/api/v1`

## 文本编码规范

仓库中的文本文件约定统一使用：

- UTF-8 无 BOM
- CRLF 行尾

## 常用命令

```bash
cd frontend
npm install
npm run type-check
npm run build
npm run dev
```

## 后续推荐优化

以下建议当前仅写入文档，不代表后端已实现：

- `precheck` 可返回标准化摘要结构，减少前端确认弹窗的本地拼装逻辑
- `submit` 可直接返回首屏可用的 evaluation snapshot，而不是只返回 `evaluationId`
- `evaluations` 详情接口可逐步引入版本号、ETag 或推送机制，用于降低 3 秒轮询带来的后端压力
