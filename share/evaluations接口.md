# 评测记录与报告接口补充说明

> 本文档是 [`API接口协议.md`](./API接口协议.md) 的评测域补充说明。  
> 精确路由、请求体、响应体和错误码以总协议为准。

## 1. 当前覆盖接口

- `GET /api/v1/evaluations`
- `GET /api/v1/evaluations/{evaluationId}`
- `POST /api/v1/evaluations/{evaluationId}/actions`

## 2. 页面交互流程

### 2.1 用户中心 `/user`

- 页面进入时调用 `GET /api/v1/evaluations`
- 前端按 `createdAt` 倒序展示记录
- 点击记录后跳转到 `/user/evaluation/{evaluationId}`

### 2.2 评测详情 `/user/evaluation/{evaluationId}`

- 页面进入时调用 `GET /api/v1/evaluations/{evaluationId}`
- 若任务处于非终态，前端可轮询详情接口获取最新快照
- 前端根据 `controls` 渲染暂停、继续、终止、取消按钮
- 用户操作时调用 `POST /api/v1/evaluations/{evaluationId}/actions`
- 动作接口直接返回最新详情快照，可用于刷新当前页面

## 3. 状态与动作补充

### 3.1 状态枚举

```text
pending | running | pausing | paused | terminating | canceling | completed | terminated | canceled | failed
```

### 3.2 终态原因枚举

```text
completed | terminated_by_user | auto_terminated_after_pause_timeout | canceled_by_user | failed
```

### 3.3 动作语义

- `pause`：允许当前数据集跑完后进入 `paused`
- `resume`：仅 `paused` 状态可恢复
- `terminate`：结束剩余队列并生成最终报告
- `cancel`：尽快取消任务，不生成最终报告

## 4. 前端显示约定

- `evaluationId` 是任务唯一公开标识。
- `datasetIds` / `runningDatasetId` 仅用于内部联调和状态跟踪。
- `datasetNames` / `runningDatasetName` / `statusText` 必须可直接展示给用户。
- 不应向用户暴露 `A1`、`C2` 这类内部数据集代码。
