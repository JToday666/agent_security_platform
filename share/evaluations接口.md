# 评测记录与报告接口

## 1. 文档目标

本文档定义当前前端在“评测记录列表 / 评测详情快照 / 任务控制 / 最终报告展示”场景下已经固定的接口契约。
`backend/` 当前尚未完整落地本文接口，因此本文以 **前端现有类型、服务层和页面行为** 为准，用于后续后端实现与联调对齐。

本文覆盖：

- `GET /api/v1/evaluations`
- `GET /api/v1/evaluations/{evaluationId}`
- `POST /api/v1/evaluations/{evaluationId}/actions`

## 2. 页面与交互流程

### 2.1 用户中心 `/user`

- 页面进入时调用 `GET /api/v1/evaluations`
- 前端按 `createdAt` 倒序展示记录
- 用户点击记录后跳转到 `/user/evaluation/{evaluationId}`

### 2.2 评测详情 `/user/evaluation/{evaluationId}`

- 页面进入时调用 `GET /api/v1/evaluations/{evaluationId}`
- 若任务处于非终态，前端每 3 秒轮询一次详情接口
- 前端根据 `controls` 渲染暂停、继续、终止、取消按钮
- 用户操作时调用 `POST /api/v1/evaluations/{evaluationId}/actions`
- 动作接口返回最新详情快照，前端直接刷新当前页状态
- 任务进入终态后停止轮询

## 3. 通用约定

### 3.1 Base URL

```text
/api/v1
```

### 3.2 通用响应包裹

成功：

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

失败：

```json
{
  "code": 40400,
  "message": "评测记录不存在。",
  "data": null
}
```

前端依赖规则：

- `code === 0` 表示成功
- `code !== 0` 表示失败
- 失败时前端优先展示 `message`
- 失败时前端只保证读取 `code` 与 `message`

### 3.3 鉴权要求

本文所有接口都需要登录，并且只能访问当前用户自己的评测任务。

### 3.4 前端显示规则

- `evaluationId` 是任务唯一标识
- `datasetIds` / `runningDatasetId` 仅用于联调和内部状态，不直接展示给用户
- `datasetNames` / `runningDatasetName` / `statusText` 必须是可直接展示给用户的公开文本
- `statusText` 不应暴露 `A1 / C2` 这类内部数据集代码

## 4. 状态与动作语义

### 4.1 状态枚举

```text
pending | running | pausing | paused | terminating | canceling | completed | terminated | canceled | failed
```

### 4.2 终态原因枚举

```text
completed | terminated_by_user | auto_terminated_after_pause_timeout | canceled_by_user | failed
```

### 4.3 动作语义

- `pause`：允许当前正在执行的数据集跑完，然后进入 `paused`
- `resume`：仅在 `paused` 状态下恢复剩余任务
- `terminate`：允许当前数据集跑完后结束剩余队列，并生成最终报告
- `cancel`：尽快取消任务，不生成最终报告

## 5. 接口定义

### 5.1 获取评测记录列表

**接口**

`GET /api/v1/evaluations`

**用途与调用时机**

- 用户中心页面初始化使用
- 返回列表摘要，不返回完整详情快照

**是否需要登录**

- 是

**请求示例**

```http
GET /api/v1/evaluations HTTP/1.1
Host: example.com
Authorization: Bearer <token>
```

**成功响应示例**

```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "evaluationId": "eval_20260403_001",
      "agentName": "安全卫士 v1.0",
      "description": "面向企业场景的多工具安全代理。",
      "createdAt": "2026-04-03T10:20:00Z",
      "updatedAt": "2026-04-03T10:35:00Z",
      "status": "running",
      "progressPercent": 45,
      "finalReportAvailable": false,
      "finalizationReason": null,
      "publicToLeaderboard": true,
      "datasetIds": ["A1", "B1", "D1"],
      "datasetNames": ["身份信息泄露", "表单数据篡改", "命令执行"],
      "submitMethod": "api",
      "score": null,
      "ownerName": "张三",
      "parameters": {
        "difficulty": 0.5,
        "timeoutMinutes": 18,
        "retryEnabled": false
      }
    }
  ]
}
```

**失败响应示例：未登录**

```json
{
  "code": 40100,
  "message": "未登录或登录已失效。",
  "data": null
}
```

**失败响应示例：服务错误**

```json
{
  "code": 50000,
  "message": "评测记录加载失败。",
  "data": null
}
```

**字段与契约说明**

- `progressPercent` 表示整体进度，范围为 `0-100`
- `finalReportAvailable` 表示最终报告是否可展示
- `datasetIds` 是内部数据集标识列表，不直接展示
- `datasetNames` 是公开数据集名称列表，供页面直接展示
- 列表接口返回摘要数据，不要求携带 `progress`、`controls` 和 `report`

### 5.2 获取单个评测详情

**接口**

`GET /api/v1/evaluations/{evaluationId}`

**用途与调用时机**

- 评测详情页初始化和轮询使用
- 返回当前任务的完整快照

**是否需要登录**

- 是

**Path 参数**

| 字段           | 类型   | 必填 | 说明        |
| -------------- | ------ | ---- | ----------- |
| `evaluationId` | string | 是   | 评测任务 ID |

**请求示例**

```http
GET /api/v1/evaluations/eval_20260403_001 HTTP/1.1
Host: example.com
Authorization: Bearer <token>
```

**成功响应示例**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "evaluationId": "eval_20260403_001",
    "agentName": "安全卫士 v1.0",
    "description": "面向企业场景的多工具安全代理。",
    "createdAt": "2026-04-03T10:20:00Z",
    "updatedAt": "2026-04-03T10:35:00Z",
    "status": "running",
    "score": null,
    "publicToLeaderboard": true,
    "datasetIds": ["A1", "B1", "D1"],
    "datasetNames": ["身份信息泄露", "表单数据篡改", "命令执行"],
    "submitMethod": "api",
    "ownerName": "张三",
    "parameters": {
      "difficulty": 0.5,
      "timeoutMinutes": 18,
      "retryEnabled": false
    },
    "progress": {
      "percent": 45,
      "totalDatasetCount": 3,
      "completedDatasetCount": 1,
      "runningDatasetId": "B1",
      "runningDatasetName": "表单数据篡改",
      "pauseDeadlineAt": null,
      "statusText": "当前正在评测数据集 表单数据篡改。"
    },
    "controls": {
      "canPause": true,
      "canResume": false,
      "canTerminate": true,
      "canCancel": true,
      "pauseUsed": false
    },
    "finalReportAvailable": false,
    "finalizationReason": null,
    "report": null
  }
}
```

**失败响应示例：无权访问**

```json
{
  "code": 40300,
  "message": "无权访问该评测任务。",
  "data": null
}
```

**失败响应示例：任务不存在**

```json
{
  "code": 40400,
  "message": "评测记录不存在。",
  "data": null
}
```

**字段与契约说明**

- 详情接口返回完整快照，列表接口返回摘要
- `controls` 足以驱动当前前端按钮显隐和禁用态
- `statusText` 需要可直接展示，不要求前端再次拼接状态机语义
- `report` 在 `finalReportAvailable=false` 时允许为 `null`
- `runningDatasetId` 是内部标识，`runningDatasetName` 是用户可见名称

**`progress` 字段说明**

| 字段                    | 说明                                              |
| ----------------------- | ------------------------------------------------- |
| `percent`               | 当前任务进度，范围 `0-100`                        |
| `totalDatasetCount`     | 本次任务总数据集数量                              |
| `completedDatasetCount` | 已完成数据集数量                                  |
| `runningDatasetId`      | 当前正在执行的数据集内部标识；无则为 `null`       |
| `runningDatasetName`    | 当前正在执行的数据集公开名称；无则为 `null`       |
| `pauseDeadlineAt`       | 进入 `paused` 后的最晚恢复时间；其他状态为 `null` |
| `statusText`            | 可直接展示给用户的状态说明文案                    |

**`controls` 字段说明**

| 字段           | 说明                       |
| -------------- | -------------------------- |
| `canPause`     | 当前是否允许暂停           |
| `canResume`    | 当前是否允许恢复           |
| `canTerminate` | 当前是否允许终止并产出报告 |
| `canCancel`    | 当前是否允许取消任务       |
| `pauseUsed`    | 是否已经使用过一次暂停机会 |

### 5.3 任务控制接口

**接口**

`POST /api/v1/evaluations/{evaluationId}/actions`

**用途与调用时机**

- 评测详情页在用户点击暂停、继续、终止、取消时调用
- 返回动作执行后的最新详情快照

**是否需要登录**

- 是

**Path 参数**

| 字段           | 类型   | 必填 | 说明        |
| -------------- | ------ | ---- | ----------- |
| `evaluationId` | string | 是   | 评测任务 ID |

**请求体字段**

| 字段     | 类型   | 必填 | 说明                                            |
| -------- | ------ | ---- | ----------------------------------------------- |
| `action` | string | 是   | 仅允许 `pause`、`resume`、`terminate`、`cancel` |

**请求体示例**

```json
{
  "action": "pause"
}
```

```json
{
  "action": "resume"
}
```

```json
{
  "action": "terminate"
}
```

```json
{
  "action": "cancel"
}
```

**成功响应示例**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "evaluationId": "eval_20260403_001",
    "agentName": "安全卫士 v1.0",
    "description": "面向企业场景的多工具安全代理。",
    "createdAt": "2026-04-03T10:20:00Z",
    "updatedAt": "2026-04-03T10:36:10Z",
    "status": "paused",
    "score": null,
    "publicToLeaderboard": true,
    "datasetIds": ["A1", "B1", "D1"],
    "datasetNames": ["身份信息泄露", "表单数据篡改", "命令执行"],
    "submitMethod": "api",
    "ownerName": "张三",
    "parameters": {
      "difficulty": 0.5,
      "timeoutMinutes": 18,
      "retryEnabled": false
    },
    "progress": {
      "percent": 45,
      "totalDatasetCount": 3,
      "completedDatasetCount": 1,
      "runningDatasetId": null,
      "runningDatasetName": null,
      "pauseDeadlineAt": "2026-04-03T11:36:10Z",
      "statusText": "任务已暂停，请在截止时间前恢复。"
    },
    "controls": {
      "canPause": false,
      "canResume": true,
      "canTerminate": true,
      "canCancel": true,
      "pauseUsed": true
    },
    "finalReportAvailable": false,
    "finalizationReason": null,
    "report": null
  }
}
```

**失败响应示例：当前状态不允许动作**

```json
{
  "code": 40901,
  "message": "当前状态不允许执行 pause 操作。",
  "data": null
}
```

**失败响应示例：暂停机会已用尽**

```json
{
  "code": 40902,
  "message": "该任务已使用过暂停机会，不能再次暂停。",
  "data": null
}
```

**失败响应示例：任务不存在**

```json
{
  "code": 40400,
  "message": "评测任务 eval_20260403_999 不存在或已被删除。",
  "data": null
}
```

**字段与契约说明**

- 成功时 `data` 结构必须与 `GET /api/v1/evaluations/{evaluationId}` 保持一致
- 后端返回动作执行后的最新任务快照，便于前端直接刷新页面
- 是否允许操作由服务端根据当前状态计算，前端不自行推导

## 6. 推荐错误码

| code    | HTTP | 场景            | 含义                 |
| ------- | ---- | --------------- | -------------------- |
| `0`     | 200  | 全部接口        | 成功                 |
| `40100` | 401  | 全部接口        | 未登录或登录失效     |
| `40300` | 403  | 详情 / 动作接口 | 无权访问他人任务     |
| `40400` | 404  | 列表以外接口    | 评测任务不存在       |
| `40901` | 409  | 动作接口        | 当前状态不允许该动作 |
| `40902` | 409  | 动作接口        | 已达到暂停次数上限   |
| `50000` | 500  | 全部接口        | 服务内部错误         |

## 7. 任务控制流程图

```mermaid
flowchart TD
    A[进入用户中心 /user] --> B[请求 evaluations 列表]
    B --> C[点击某条记录]
    C --> D[进入 /user/evaluation/{evaluationId}]
    D --> E[请求 evaluation 详情]
    E --> F{是否终态}
    F -->|否| G[每 3 秒轮询详情]
    F -->|是| H[停止轮询并展示最终状态]
    E --> I[根据 controls 渲染按钮]
    I --> J[用户触发 pause resume terminate cancel]
    J --> K[调用 actions 接口]
    K -->|成功| L[使用返回的最新快照直接刷新页面]
    K -->|失败| M[展示错误 message]
    G --> E
    L --> F
```

## 8. 后续推荐优化

以下内容仅为推荐方向，不代表后端已实现：

- 详情接口可强化 `updatedAt` 或 `version` 的语义，便于前端做轮询去重和乐观刷新
- 可逐步引入 `ETag`、长轮询、SSE 或 WebSocket，降低 3 秒轮询对后端的压力
- 若后续评测记录量显著增长，列表接口可增加分页与筛选能力，但应保持当前前端默认使用的摘要字段稳定
