# 数据集与提交接口补充说明

> 本文档是 [`API接口协议.md`](./API接口协议.md) 的数据集与提交域补充说明。  
> 精确路由、请求体、响应体和错误码以总协议为准。

## 1. 当前覆盖接口

- `GET /api/v1/datasets/catalog`
- `GET /api/v1/datasets/{datasetId}`
- `GET /api/v1/agents/submit-meta`
- `POST /api/v1/agents/precheck`
- `POST /api/v1/agents/submit`

## 2. 页面调用时机

### 2.1 数据集列表页 `/dataset`

- 页面挂载时调用 `GET /api/v1/datasets/catalog`
- 点击某个数据集后跳转到 `/dataset/{datasetId}`
- 详情页根据路由参数调用 `GET /api/v1/datasets/{datasetId}`

### 2.2 提交页 `/user/submit`

- 页面初始化时调用 `GET /api/v1/agents/submit-meta`
- 页面初始化时调用一次 `GET /api/v1/datasets/catalog`
- 点击“提交任务”时，前端先调用 `POST /api/v1/agents/precheck`
- 用户确认后再调用 `POST /api/v1/agents/submit`
- 提交成功后跳转到 `/user/evaluation/{evaluationId}`

## 3. 领域补充约定

- `catalog` 不接收 `difficulty` query 参数。
- `difficulty` 只保留在 `precheck` / `submit` 的 `parameters.difficulty` 中。
- `datasetId` / `datasetIds` 是内部公开标识，只用于路由、缓存和接口传参。
- 用户界面应优先显示后端返回的 `name`，不要直接向用户展示内部代码。
- `POST /api/v1/agents/submit` 对同一用户 + 同一 `requestId` 提供幂等保证。
- `submitMethod = "api"` 与 `submitMethod = "docker"` 的配置对象互斥。
