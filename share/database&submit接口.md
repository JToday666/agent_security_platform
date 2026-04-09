# 数据集与提交接口补充说明

## 当前有效行为

本文件描述的是前端当前真实生效的运行方式，用于补充 [`API接口协议.md`](./API接口协议.md)。

### 默认真实后端

默认情况下，以下接口都走真实后端：

- `GET /api/v1/datasets/catalog`
- `GET /api/v1/datasets/{datasetId}`
- `GET /api/v1/agents/submit-meta`
- `POST /api/v1/agents/precheck`
- `POST /api/v1/agents/submit`

### 显式 Mock 开关

只有在设置 `VITE_ENABLE_API_MOCK=true` 时，提交与评测 mock 才会启用。

默认值：

- `VITE_ENABLE_API_MOCK=false`

## 页面调用顺序

### 数据集列表页 `/dataset`

- 页面进入时请求 `GET /api/v1/datasets/catalog`
- 点击某个数据集后进入 `/dataset/{datasetId}`
- 详情页请求 `GET /api/v1/datasets/{datasetId}`

### 提交页 `/user/submit`

页面初始化时依次准备：

- `GET /api/v1/agents/submit-meta`
- `GET /api/v1/datasets/catalog`

用户点击提交时：

1. 先调用 `POST /api/v1/agents/precheck`
2. 用户确认后再调用 `POST /api/v1/agents/submit`
3. 成功后跳转 `/user/evaluation/{evaluationId}`

## 缓存与持久化边界

### 页面生命周期内内存缓存

允许缓存：

- `datasets/catalog`
- `datasets/{datasetId}`
- `agents/submit-meta`

缓存只在当前前端运行生命周期内有效，刷新页面后失效。

### 禁止 durable localStorage 持久化

真实 API 模式下，以下结果不写入 localStorage：

- precheck 结果
- submit 结果
- 评测记录快照
- 评测详情快照

### 允许持久化

- 提交草稿
- token
- 登录回跳地址
- 非业务真相类 UI 状态

## 前端字段约定

- 列表与详情 API 不再接收 `difficulty` query 参数
- `difficulty` 只保留在 `precheck` / `submit` 的 `parameters.difficulty`
- 前端表单字段仍使用 `selectedDatasetIds`
- 发给后端前统一适配为 `datasetIds`

## 显示约定

- 用户界面优先显示公开名称，不直接展示内部 dataset code
- 后端字段为空、缺失、`null`、空字符串时，页面必须进入降级显示
- 不允许出现裸 `undefined`、`null` 或因空字段导致页面崩溃
