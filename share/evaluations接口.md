# evaluations接口

## 1. 文档目标与统一结论

本文档面向后端开发和联调人员，定义评测列表、评测详情、任务控制相关接口契约。

当前 `backend/` 仓库尚未实现本文涉及的评测接口，因此本文档用于后端实现和前后端联调定稿。

本文档覆盖以下接口：

- `GET /api/v1/evaluations`
- `GET /api/v1/evaluations/{evaluationId}`
- `POST /api/v1/evaluations/{evaluationId}/actions`

### 1.1 统一结论

- v1 **不单独引入 `reportId`**
- `evaluationId` 既是任务 ID，也是评测详情页和最终报告的唯一主键
- “报告”不是独立资源，而是 `evaluation` 进入终态后的一个视图
- 提交成功后，前端直接跳转到 `/user/evaluation/{evaluationId}`
- 旧报告页入口已移除；未知前端路径统一进入 404 页面

---

## 2. 关联页面与业务流程

### 2.1 用户中心评测列表

**场景**：用户访问 `/user`，查看自己的评测任务列表。

```text
1. 用户访问 /user
   ↓
2. 页面挂载 → 调用 GET /api/v1/evaluations
   ↓
3. 后端返回当前用户的评测任务列表
   ↓
4. 前端按 createdAt 倒序展示
   ↓
5. 用户点击某条记录 → 跳转到 /user/evaluation/{evaluationId}
```

### 2.2 评测详情页与报告页一体化流程

**场景**：用户查看某个任务的当前进度或最终报告。

```text
1. 用户访问 /user/evaluation/{evaluationId}
   ↓
2. 页面挂载 → 调用 GET /api/v1/evaluations/{evaluationId}
   ↓
3. 若状态是非终态，则前端每 3 秒轮询一次详情接口
   ↓
4. 前端根据 controls 渲染“暂停 / 继续 / 终止 / 取消”按钮
   ↓
5. 用户点击任务控制按钮时，调用 POST /api/v1/evaluations/{evaluationId}/actions
   ↓
6. 后端返回最新任务快照，前端覆盖页面状态
   ↓
7. 当状态进入终态后，前端停止轮询
   ├─ completed / terminated：展示最终报告
   ├─ canceled：展示任务终止信息，不展示最终报告
   └─ failed：展示失败信息，不展示最终报告
```

---

## 3. 通用约定

### 3.1 Base URL

前端请求层默认使用：

```text
/api/v1
```

### 3.2 通用响应结构

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

失败示例：

```json
{
  "code": 40400,
  "message": "评测任务 eval_123 不存在。",
  "data": null
}
```

### 3.3 鉴权要求

本文所有接口都必须登录后调用，并且只能访问当前用户自己的评测任务。

### 3.4 轮询约定

- 前端在任务处于非终态时，默认每 3 秒轮询一次 `GET /api/v1/evaluations/{evaluationId}`
- 终态包括：`completed`、`terminated`、`canceled`、`failed`
- 进入终态后停止轮询

---

## 4. 状态集合与动作语义

### 4.1 状态集合

本轮状态枚举统一定稿为：

```text
pending | running | pausing | paused | terminating | canceling | completed | terminated | canceled | failed
```

### 4.2 状态含义

| 状态          | 含义                                     | 是否终态 | 是否有最终报告 |
| ------------- | ---------------------------------------- | -------- | -------------- |
| `pending`     | 任务已创建，等待调度                     | 否       | 否             |
| `running`     | 正在评测数据集                           | 否       | 否             |
| `pausing`     | 已收到暂停请求，等待当前数据集跑完后暂停 | 否       | 否             |
| `paused`      | 当前任务已暂停，等待用户继续、终止或取消 | 否       | 否             |
| `terminating` | 已收到终止请求，等待当前数据集跑完后结束 | 否       | 否             |
| `canceling`   | 已收到取消请求，正在尽快中断执行         | 否       | 否             |
| `completed`   | 所有数据集评测完成                       | 是       | 是             |
| `terminated`  | 用户终止或暂停超时后结束剩余队列         | 是       | 是             |
| `canceled`    | 用户取消任务，任务直接中断               | 是       | 否             |
| `failed`      | 系统异常导致任务失败                     | 是       | 否             |

### 4.3 推荐的 finalizationReason 枚举

终态下推荐返回：

```text
completed | terminated_by_user | auto_terminated_after_pause_timeout | canceled_by_user | failed
```

非终态时，`finalizationReason` 返回 `null`。

### 4.4 动作语义

#### pause

- 含义：暂停当前任务，但允许当前正在执行的数据集跑完
- 一个任务最多只能暂停一次
- 进入 `paused` 后，后端返回 `pauseDeadlineAt`
- 如果用户在 1 小时内没有选择继续、终止或取消，则系统自动转为 `terminated`

#### resume

- 含义：继续执行尚未评测的数据集
- 只允许在 `paused` 状态下调用
- 恢复后 `pauseUsed` 保持为 `true`

#### terminate

- 含义：允许当前数据集跑完，然后结束剩余队列
- 会生成最终报告
- 在 `paused` 状态下调用时，可直接结束剩余队列并生成最终报告

#### cancel

- 含义：尽快取消当前任务，不再生成最终报告
- 任务终态为 `canceled`
- 详情页保留任务信息和终止原因，但 `report=null`

### 4.5 推荐动作可用性

最终以前端读取的 `controls` 为准；下表是推荐默认行为：

| 状态          | 推荐可用动作                    |
| ------------- | ------------------------------- |
| `pending`     | `cancel`                        |
| `running`     | `pause`、`terminate`、`cancel`  |
| `pausing`     | 无                              |
| `paused`      | `resume`、`terminate`、`cancel` |
| `terminating` | 无                              |
| `canceling`   | 无                              |
| 终态          | 无                              |

---

## 5. 接口定义

### 5.1 获取当前用户评测记录

`GET /api/v1/evaluations`

#### 5.1.1 用途

- 用户中心 `/user` 页面展示评测记录列表

#### 5.1.2 成功响应

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
      "datasetNames": ["身份信息泄露", "指令篡改", "越权工具调用"],
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

#### 5.1.3 字段说明

- `progressPercent`：当前进度，范围 `0-100`，整数
- `finalReportAvailable`：是否已有最终报告
- `finalizationReason`：终态原因，非终态为 `null`
- `score`：最终得分；未生成最终报告时可为 `null`

#### 5.1.4 排序要求

后端应按 `createdAt` 倒序返回，最新任务优先。

#### 5.1.5 常见失败响应

```json
{
  "code": 40100,
  "message": "未登录或登录失效，请先登录。",
  "data": null
}
```

```json
{
  "code": 50000,
  "message": "无法获取评测记录，服务暂时不可用。",
  "data": null
}
```

### 5.2 获取单个评测详情与报告

`GET /api/v1/evaluations/{evaluationId}`

#### 5.2.1 用途

- 评测详情页 `/user/evaluation/:evaluationId`
- 统一承载“进行中的任务视图”和“终态报告视图”

#### 5.2.2 成功响应

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
    "datasetNames": ["身份信息泄露", "指令篡改", "越权工具调用"],
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
      "runningDatasetName": "指令篡改",
      "pauseDeadlineAt": null,
      "statusText": "当前正在评测数据集 B1（指令篡改）"
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

#### 5.2.3 progress 字段定义

| 字段                    | 说明                                              |
| ----------------------- | ------------------------------------------------- |
| `percent`               | 当前任务进度，范围 `0-100`，整数，由后端计算      |
| `totalDatasetCount`     | 本次任务总数据集数量                              |
| `completedDatasetCount` | 已完成数据集数量                                  |
| `runningDatasetId`      | 当前正在执行的数据集 ID；无则为 `null`            |
| `runningDatasetName`    | 当前正在执行的数据集名称；无则为 `null`           |
| `pauseDeadlineAt`       | 进入 `paused` 后的最晚恢复时间；其他状态为 `null` |
| `statusText`            | 供前端直接展示的状态说明文案                      |

前端只负责展示和动画平滑，不自行推断业务进度。

#### 5.2.4 controls 字段定义

| 字段           | 说明                               |
| -------------- | ---------------------------------- |
| `canPause`     | 当前是否允许暂停                   |
| `canResume`    | 当前是否允许继续                   |
| `canTerminate` | 当前是否允许终止                   |
| `canCancel`    | 当前是否允许取消                   |
| `pauseUsed`    | 当前任务是否已经使用过一次暂停机会 |

前端根据 `controls` 决定按钮显隐和禁用状态，不自行硬编码状态机。

#### 5.2.5 report 字段定义

`report` 固定为对象或 `null`。推荐结构如下：

```json
{
  "generatedAt": "2026-04-03T11:10:00Z",
  "summary": "本次评测共覆盖 3 个数据集，核心安全指标表现稳定。",
  "warnings": ["建议继续优化长上下文场景下的越权调用边界。"],
  "metrics": [
    {
      "name": "攻击检测率",
      "value": "96%",
      "percentage": 96,
      "description": "识别恶意提示与异常工具响应的能力。"
    }
  ]
}
```

生成规则：

- `completed`：`report` 必须存在
- `terminated`：`report` 必须存在
- `canceled`：`report` 必须为 `null`
- `failed`：v1 默认 `report` 为 `null`
- 非终态：`report` 为 `null`

#### 5.2.6 常见失败响应

```json
{
  "code": 40100,
  "message": "未登录或登录失效，请先登录。",
  "data": null
}
```

```json
{
  "code": 40300,
  "message": "无权查看该评测，只能查看自己的评测。",
  "data": null
}
```

```json
{
  "code": 40400,
  "message": "评测任务 eval_123 不存在或已被删除。",
  "data": null
}
```

### 5.3 任务控制接口

`POST /api/v1/evaluations/{evaluationId}/actions`

#### 5.3.1 用途

- 对未完成任务执行 `pause / resume / terminate / cancel`
- 返回最新任务快照，便于前端直接覆盖当前页面状态

#### 5.3.2 请求体

```json
{
  "action": "pause"
}
```

`action` 只允许：

- `pause`
- `resume`
- `terminate`
- `cancel`

#### 5.3.3 成功响应

响应的 `data` 结构与 `GET /api/v1/evaluations/{evaluationId}` 完全一致，推荐直接返回最新任务快照。

#### 5.3.4 关键语义

- `pause`：等待当前数据集跑完后转入 `paused`
- `resume`：仅在 `paused` 下恢复剩余队列
- `terminate`：当前数据集跑完后结束剩余队列并生成最终报告
- `cancel`：立即取消任务，不生成最终报告

#### 5.3.5 常见失败响应

```json
{
  "code": 40901,
  "message": "当前状态不允许执行 pause 操作。",
  "data": null
}
```

```json
{
  "code": 40902,
  "message": "该任务已使用过暂停机会，不能再次暂停。",
  "data": null
}
```

```json
{
  "code": 40400,
  "message": "评测任务 eval_123 不存在或已被删除。",
  "data": null
}
```

---

## 6. 前端交互约定

- 提交成功后，前端默认跳转到 `/user/evaluation/{evaluationId}`
- 列表页默认进入时加载一次，不自动轮询
- 非终态任务详情页默认每 3 秒轮询一次
- 终态后停止轮询
- 列表页使用 `progressPercent` 展示进度
- 详情页使用 `progress.percent` 展示进度
- 详情页根据 `controls` 决定按钮显隐和禁用状态
- `pause`、`terminate`、`cancel` 都必须弹确认框
- `resume` 直接执行，不额外弹确认框
- `cancel` 为高风险动作，前端使用危险样式
- `finalReportAvailable=true` 且 `report` 存在时，前端展示最终报告
- `canceled` 或 `failed` 时，前端展示任务终态说明，不展示报告区

---

## 7. 推荐错误码与前端处理

| code    | HTTP 状态 | API 位置                                                  | 含义                 | 前端处理建议                 |
| ------- | --------- | --------------------------------------------------------- | -------------------- | ---------------------------- |
| `0`     | 200       | 所有                                                      | 成功                 | 无特殊处理                   |
| `40100` | 401       | 所有                                                      | 未登录或登录失效     | 触发登录流程                 |
| `40300` | 403       | `GET /evaluations/{id}`、`POST /evaluations/{id}/actions` | 无权访问他人任务     | 展示“无权访问”               |
| `40400` | 404       | 所有                                                      | 评测任务不存在       | 展示“任务不存在”             |
| `40901` | 409       | `POST /evaluations/{id}/actions`                          | 当前状态不允许该动作 | 刷新详情并提示当前状态已变化 |
| `40902` | 409       | `POST /evaluations/{id}/actions`                          | 已达到暂停次数上限   | 提示该任务不能再次暂停       |
| `50000` | 500       | 所有                                                      | 服务器内部错误       | 显示“服务异常，请稍后重试”   |

---

## 8. 附录 A：核心 TypeScript 类型

### A.1 评测列表项

```typescript
interface EvaluationRecord {
  evaluationId: string;
  agentName: string;
  description?: string;
  createdAt: string;
  updatedAt: string;
  status:
    | "pending"
    | "running"
    | "pausing"
    | "paused"
    | "terminating"
    | "canceling"
    | "completed"
    | "terminated"
    | "canceled"
    | "failed";
  progressPercent: number;
  finalReportAvailable: boolean;
  finalizationReason:
    | "completed"
    | "terminated_by_user"
    | "auto_terminated_after_pause_timeout"
    | "canceled_by_user"
    | "failed"
    | null;
  publicToLeaderboard: boolean;
  datasetIds: string[];
  datasetNames: string[];
  submitMethod: "api" | "docker";
  score: number | null;
  ownerName: string;
  parameters: {
    difficulty: number;
    timeoutMinutes: number;
    retryEnabled: boolean;
  };
}
```

### A.2 评测详情与任务控制

```typescript
interface EvaluationDetail extends Omit<EvaluationRecord, "progressPercent"> {
  progress: {
    percent: number;
    totalDatasetCount: number;
    completedDatasetCount: number;
    runningDatasetId: string | null;
    runningDatasetName: string | null;
    pauseDeadlineAt: string | null;
    statusText: string;
  };
  controls: {
    canPause: boolean;
    canResume: boolean;
    canTerminate: boolean;
    canCancel: boolean;
    pauseUsed: boolean;
  };
  report: EvaluationReport | null;
}

interface EvaluationReport {
  generatedAt: string;
  summary: string;
  warnings: string[];
  metrics: EvaluationMetric[];
}

interface EvaluationMetric {
  name: string;
  value: string;
  percentage: number;
  description: string;
}

interface EvaluationActionRequest {
  action: "pause" | "resume" | "terminate" | "cancel";
}
```
