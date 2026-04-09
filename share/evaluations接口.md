# 评测记录与详情接口补充说明

## 当前有效行为

本文件补充说明前端当前对评测接口的真实消费方式。

### 默认真实后端

默认情况下，以下接口走真实后端：

- `GET /api/v1/evaluations`
- `GET /api/v1/evaluations/{evaluationId}`
- `POST /api/v1/evaluations/{evaluationId}/actions`

只有 `VITE_ENABLE_API_MOCK=true` 时，评测 mock 才会启用。

## 页面调用方式

### 评测记录页 `/user`

- 页面进入时调用 `GET /api/v1/evaluations`
- 列表按创建时间倒序展示
- 点击记录跳转 `/user/evaluation/{evaluationId}`

### 评测详情页 `/user/evaluation/{evaluationId}`

- 页面进入时调用 `GET /api/v1/evaluations/{evaluationId}`
- 非终态任务继续轮询详情接口，轮询间隔为 10 分钟
- 页面根据 `controls` 决定是否显示 `pause / resume / terminate / cancel`
- 动作请求通过 `POST /api/v1/evaluations/{evaluationId}/actions`

## 缓存与持久化边界

### 不做 durable localStorage 持久化

真实 API 模式下，以下内容不写入 localStorage：

- 评测记录列表
- 评测详情快照
- 动作结果快照

### 状态真相源

以下字段以后端返回为准：

- `status`
- `progress`
- `controls`
- `report`

前端不再把本地拼装结果作为 live 模式下的真相源。

## 报告字段对齐

前端当前按以下结构消费报告：

- `reportStatus`
- `summary`
- `reportUri`

详情页展示重点：

- 汇总统计
- 风险分类聚合
- 风险等级聚合
- 攻击等级聚合
- 报告链接

### 降级显示

当 `report` 不存在或字段缺失时：

- 页面进入“无报告/生成中/不可用”状态
- 不假设报告一定存在
- 不直接渲染空数组、空链接或旧格式字段

## 状态与动作约束

当前状态集合：

```text
pending | running | pausing | paused | terminating | canceling | completed | terminated | canceled | failed
```

终态原因集合：

```text
completed | terminated_by_user | auto_terminated_after_pause_timeout | canceled_by_user | failed
```

动作显示与可执行性只以后端 `controls` 为准，不由前端自行推断。
