# database&submit接口

## 1. 文档目标

本文档面向后端开发和联调人员，描述当前前端在“数据集”和“提交智能体”相关页面上已经固定下来的接口契约，以及本轮接口定稿后的推荐实现方式。

当前 `backend/` 仓库里尚未实现本文涉及的 `datasets / agents / evaluations` 相关接口，因此本文档是后端实现与前后端联调的契约源。

本文档本轮仅覆盖以下接口：

- `GET /api/v1/agents/submit-meta`
- `GET /api/v1/datasets/catalog`
- `GET /api/v1/datasets/{datasetId}`
- `POST /api/v1/agents/precheck`
- `POST /api/v1/agents/submit`

评测相关接口已整体迁移到 `share/evaluations接口.md`，本文只保留“提交成功后跳转评测详情页”的关系说明，不再重复定义评测接口字段。

## 2. 关联页面与业务流程

### 2.1 数据集浏览流程

**场景**：用户从导航栏进入数据集列表页，查看目录和详情。

**时序步骤**：

```text
1. 用户访问 /dataset
   ↓
2. 页面挂载 → 调用 GET /api/v1/datasets/catalog
   ↓
3. 前端展示目录树状结构
   ↓
4. 用户点击某个数据集，例如 “身份信息泄露 (A1)”
   ↓
5. 跳转到 /dataset/A1
   ↓
6. 页面挂载 → 调用 GET /api/v1/datasets/A1
   ↓
7. 前端渲染详情、重点、场景、媒体和资源链接
```

**前端依赖行为**：

- 列表页不传 `difficulty`
- 详情页严格按路由参数 `datasetId` 发请求
- 资源不存在时返回 `40400`
- 资源存在但服务异常时返回 `50000`

### 2.2 提交智能体完整流程

**场景**：用户从导航进入提交页，填写表单并创建评测任务。

**时序步骤**：

```text
1. 用户访问 /user/submit
   ↓
2. 页面初始化
   ├─ 调用 GET /api/v1/agents/submit-meta
   ├─ 按默认 difficulty 调用 GET /api/v1/datasets/catalog?difficulty=...
   └─ 渲染提交表单
   ↓
3. 用户填写或修改表单
   ├─ 智能体名称、描述、提交方式
   ├─ API 或 Docker 字段
   ├─ parameters
   └─ 数据集选择
   ↓
4. 前端按规范化后的 payload 生成或复用 requestId
   ├─ requestId 与 payloadDigest 一起持久化到草稿态
   └─ 若关键字段变化，则旧 requestId 失效并重新生成
   ↓
5. 用户点击 “提交任务”
   ↓
6. 前端先做本地校验，再调用 POST /api/v1/agents/precheck
   └─ 请求体与正式提交完全一致
   ↓
7. 前端弹出确认窗口
   ├─ warnings 非空时使用警告样式
   └─ warnings 为空时使用普通确认样式
   ↓
8. 用户点击 “确认提交”
   ↓
9. 前端调用 POST /api/v1/agents/submit
   ├─ 使用与 precheck 相同的请求体
   ├─ 使用同一个 requestId
   └─ 后端再次校验并创建任务
   ↓
10. 提交成功
   ├─ 返回 evaluationId
   ├─ 前端清空草稿和 pendingRequest
   └─ 跳转到 /user/evaluation/{evaluationId}
```

**关键点**：

- 页面主按钮文案统一为“提交任务”
- “预检查”是内部技术步骤，不作为用户显式按钮概念暴露
- `precheck` 和 `submit` 使用同一 `requestId`
- 用户刷新、断网重试、重复点击时，只要 payload 未变化，就复用同一个 `requestId`
- 前端只保留当前规范页面路径；历史旧地址不再兼容，未知路径统一进入 404 页面

### 2.3 提交成功后的后续流程

`POST /api/v1/agents/submit` 成功后，前端跳转到 `/user/evaluation/{evaluationId}`。评测详情、轮询、任务控制等接口定义，详见 `share/evaluations接口.md`。

### 2.4 页面与调用时机对照表

| 页面                             | 调用的接口                                    | 调用时机                 | 是否需登录 |
| -------------------------------- | --------------------------------------------- | ------------------------ | ---------- |
| `/dataset`                       | `GET /api/v1/datasets/catalog`                | 页面挂载                 | 否         |
| `/dataset/:datasetId`            | `GET /api/v1/datasets/{datasetId}`            | 路由参数变化             | 否         |
| `/user/submit`                   | `GET /api/v1/agents/submit-meta`              | 页面初始化               | 否         |
| `/user/submit`                   | `GET /api/v1/datasets/catalog?difficulty=...` | 初始化、难度变化         | 否         |
| `/user/submit`                   | `POST /api/v1/agents/precheck`                | 首击“提交任务”后         | 是         |
| `/user/submit`                   | `POST /api/v1/agents/submit`                  | 确认弹窗点击“确认提交”后 | 是         |
| `/user/evaluation/:evaluationId` | 详见 `share/evaluations接口.md`               | 提交成功后跳转           | 是         |

## 3. 通用约定

### 3.1 Base URL

前端请求层默认使用：

```text
/api/v1
```

### 3.2 通用响应结构

前端统一按以下 envelope 解析响应：

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
  "code": 40002,
  "message": "参数超出允许范围。",
  "data": null
}
```

前端依赖规则如下：

- `code === 0` 表示成功
- `code !== 0` 表示业务失败
- 失败时优先展示 `message`
- `data` 在失败时允许为 `null`

### 3.3 HTTP 状态与业务错误码

当前前端兼容两种错误形式：

- HTTP 200 + envelope 中 `code != 0`
- HTTP 非 2xx，响应体中仍带 `message` 或 `detail`

推荐后端统一返回 envelope，并在鉴权失败时使用 HTTP 401，在资源不存在时使用 HTTP 404，在幂等冲突时使用 HTTP 409。

### 3.4 鉴权要求

| 接口                               | 是否需要登录 | 说明                                 |
| ---------------------------------- | ------------ | ------------------------------------ |
| `GET /api/v1/agents/submit-meta`   | 否           | 提交页初始化依赖                     |
| `GET /api/v1/datasets/catalog`     | 否           | 数据集列表页、提交页都依赖           |
| `GET /api/v1/datasets/{datasetId}` | 否           | 数据集详情页依赖                     |
| `POST /api/v1/agents/precheck`     | 是           | 提交前预检查，需要绑定当前用户上下文 |
| `POST /api/v1/agents/submit`       | 是           | 正式创建评测任务，必须归属当前用户   |

### 3.5 幂等约定与 requestId 生命周期

`POST /api/v1/agents/submit` 必须支持幂等。

#### 3.5.1 requestId 的定位

- `requestId` 是幂等键，不是业务主键
- `evaluationId` 才是后端生成的正式任务主键
- 同一用户 + 同一 `requestId` 的重复提交，后端必须返回同一个 `evaluationId`

#### 3.5.2 为什么 requestId 继续由前端生成

- 幂等最关键的场景，是“第一次请求已到达后端，但前端没有拿到成功响应”
- 如果 `requestId` 由后端生成，那么第一次响应一旦丢失，前端就拿不到这个键，后续无法对同一次提交做幂等重试
- `requestId` 还需要跨 `precheck` 和 `submit` 共享，表示“同一次用户提交意图”，这同样要求它在调用 `precheck` 前就已经存在

#### 3.5.3 后端如何处理前端生成的 requestId

推荐后端在数据库层：

- 以 `(user_id, request_id)` 建唯一约束或唯一索引
- 首次 `submit` 创建任务并生成 `evaluationId`
- 后续同用户、同 `requestId` 的重复请求直接返回同一个 `evaluationId`
- 若同一 `(user_id, request_id)` 对应的关键业务参数不一致，则返回 `40900`

#### 3.5.4 requestId 的前端生命周期

- 当前端首次形成可提交的规范化 payload 时生成 `requestId`
- `requestId` 与 `payloadDigest` 一起保存在草稿态的 `pendingRequest` 中
- payload 不变时，刷新页面、重新进入页面、重复点击都复用同一个 `requestId`
- 关键字段变化时，旧 `requestId` 失效并重新生成
- 提交成功后，前端清除 `pendingRequest`

#### 3.5.5 payloadDigest 的推荐覆盖字段

`payloadDigest` 应基于规范化后的业务字段生成，至少覆盖：

- `agentName`
- `description`
- `submitMethod`
- `api.baseUrl` 或 `docker.imageUri`
- `parameters`
- `publicToLeaderboard`
- 排序去重后的 `datasetIds`

不应持久化到摘要中的敏感字段：

- `api.token`
- `docker.password`

### 3.6 Frontend Mock 与真实 API 切换机制

| 环境变量                       | 默认值    | 说明                                              |
| ------------------------------ | --------- | ------------------------------------------------- |
| `VITE_USE_LIVE_REFERENCE_API`  | `false`   | `submit-meta`、数据集相关接口是否走真实后端       |
| `VITE_USE_LIVE_SUBMISSION_API` | `false`   | `precheck`、`submit` 和评测相关接口是否走真实后端 |
| `VITE_API_BASE_URL`            | `/api/v1` | 后端 API 基础 URL                                 |

## 4. 数据集接口

### 4.1 获取数据集目录

`GET /api/v1/datasets/catalog`

#### 4.1.1 用途

- 数据集列表页展示完整目录
- 提交页按当前 `difficulty` 刷新“当前可选数据集”

#### 4.1.2 Query 参数

| 参数         | 类型                  | 必填 | 说明                                  |
| ------------ | --------------------- | ---- | ------------------------------------- |
| `difficulty` | `number` 或数字字符串 | 否   | 攻击难度，范围 `0` 到 `1`，步长 `0.1` |

示例：

```text
GET /api/v1/datasets/catalog?difficulty=0.5
```

#### 4.1.3 成功响应

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "catalogVersion": "2026-04-01T10:00:00Z",
    "categoryCount": 4,
    "subcategoryCount": 8,
    "categories": [
      {
        "categoryId": "A",
        "name": "身份与权限",
        "meaning": "身份冒用、越权访问与权限边界失守",
        "description": "覆盖身份伪装、越权调用与权限链污染等风险。",
        "sort": 1,
        "enabled": true,
        "subcategoryCount": 2,
        "subcategories": [
          {
            "datasetId": "A1",
            "name": "身份信息泄露",
            "shortDescription": "检测对个人身份敏感信息的保护能力。",
            "sampleCount": 960,
            "updatedAt": "2026-04-01T10:00:00Z",
            "enabled": true
          }
        ]
      }
    ]
  }
}
```

#### 4.1.4 约定

- 列表页调用时不传 `difficulty`
- 提交页调用时带上当前 `difficulty`
- 传 `difficulty` 时，后端返回该难度下可用的数据集子集
- 若某个大类在当前难度下没有任何可用数据集，应从结果中移除
- `categoryCount` 和 `subcategoryCount` 必须基于过滤后结果重新计算
- `catalogVersion` 用于草稿同步和目录版本变更提示

#### 4.1.5 常见失败响应

```json
{
  "code": 40002,
  "message": "参数 difficulty 必须在 0 到 1 之间，步长为 0.1。",
  "data": null
}
```

```json
{
  "code": 50000,
  "message": "无法获取数据集目录，请稍后重试。",
  "data": null
}
```

### 4.2 获取单个数据集详情

`GET /api/v1/datasets/{datasetId}`

#### 4.2.1 用途

- 数据集详情页直接加载详情内容

#### 4.2.2 成功响应

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "datasetId": "A1",
    "name": "身份信息泄露",
    "category": {
      "categoryId": "A",
      "name": "身份与权限",
      "meaning": "身份冒用、越权访问与权限边界失守"
    },
    "shortDescription": "检测对个人身份敏感信息的保护能力。",
    "fullDescription": "该数据集重点覆盖真实身份、伪造身份、越权查询与工具结果泄露等场景。",
    "sampleCount": 960,
    "updatedAt": "2026-04-01T10:00:00Z",
    "highlights": ["覆盖高频身份查询与诱导泄露路径"],
    "scenarios": ["攻击者诱导系统披露个人身份信息"],
    "resources": [
      {
        "label": "查看评测说明",
        "url": "https://example.com/docs/datasets/A1",
        "type": "docs"
      }
    ],
    "media": [
      {
        "mediaId": "A1-image",
        "type": "image",
        "title": "身份信息泄露样例概览",
        "description": "用于展示该评测项的输入结构和预期安全边界。",
        "url": "https://example.com/media/A1.png",
        "coverUrl": null,
        "sort": 1
      }
    ]
  }
}
```

#### 4.2.3 约定

- `datasetId`、`name`、`shortDescription`、`sampleCount`、`updatedAt` 应与目录接口中同一数据集保持一致
- `resources` 即使为空，也应返回空数组而不是省略字段
- `media[].type` 当前只约定 `image`、`video`

#### 4.2.4 常见失败响应

```json
{
  "code": 40400,
  "message": "数据集 A999 不存在或已下线。",
  "data": null
}
```

```json
{
  "code": 50000,
  "message": "数据集详情加载失败，请稍后重试。",
  "data": null
}
```

## 5. 提交前元数据接口

### 5.1 获取提交参数元数据

`GET /api/v1/agents/submit-meta`

#### 5.1.1 用途

- 决定提交页支持哪些提交方式
- 决定 `difficulty / timeoutMinutes / retryEnabled / publicToLeaderboard` 的默认值和范围
- 决定前端是否展示超时软提示

#### 5.1.2 正式成功响应

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "supportedMethods": ["api", "docker"],
    "difficulty": {
      "min": 0,
      "max": 1,
      "step": 0.1,
      "default": 0.5
    },
    "timeoutMinutes": {
      "min": 15,
      "max": 30,
      "step": 1,
      "default": 15,
      "recommendedMax": 20
    },
    "retryEnabled": {
      "default": false
    },
    "publicToLeaderboard": {
      "default": true
    }
  }
}
```

#### 5.1.3 协议约束

前端**当前内部消费模型已经固定为扁平新结构**。也就是说，提交页内部的 store、validator、组件 props 和页面渲染逻辑都直接消费：

```json
{
  "supportedMethods": ["api", "docker"],
  "difficulty": { "min": 0, "max": 1, "step": 0.1, "default": 0.5 },
  "timeoutMinutes": {
    "min": 15,
    "max": 30,
    "step": 1,
    "default": 15,
    "recommendedMax": 20
  },
  "retryEnabled": { "default": false },
  "publicToLeaderboard": { "default": true }
}
```

**正式结论**：

- 后端正式契约只返回扁平新结构
- 旧 `parameterMeta` 协议已废弃，不再作为过渡兼容输入
- 如果接口仍返回旧结构，前端会在提交页初始化阶段直接失败，并视为接口契约不匹配

#### 5.1.4 常见失败响应

```json
{
  "code": 50000,
  "message": "无法获取提交元数据，服务暂时不可用。",
  "data": null
}
```

## 6. 提交接口

### 6.1 通用请求体

`POST /api/v1/agents/precheck` 和 `POST /api/v1/agents/submit` 使用**同一请求体**。

前端内部状态名仍然是 `selectedDatasetIds`，但发给后端前必须转换为 `datasetIds`。

```json
{
  "agentName": "安全卫士 v1.0",
  "description": "面向企业场景的多工具安全代理。",
  "submitMethod": "api",
  "api": {
    "baseUrl": "https://example.com/agent/run",
    "token": "sk-xxxx"
  },
  "docker": null,
  "parameters": {
    "difficulty": 0.5,
    "timeoutMinutes": 15,
    "retryEnabled": false
  },
  "publicToLeaderboard": true,
  "datasetIds": ["A1", "B1", "D1"],
  "requestId": "8c5ecb4e-79f9-47eb-84d8-a8aa0d53f27f"
}
```

关键约束：

- `agentName` 必填，长度 `1-100`
- `submitMethod` 仅支持 `api`、`docker`
- `api.baseUrl` 在 API 模式下必填，且必须为合法 `http/https` URL
- `docker.imageUri` 在 Docker 模式下必填
- `datasetIds` 至少 `1` 个，最多 `100` 个，必须去重且全部有效
- `requestId` 必填，长度建议 `8-128`，只允许字母、数字、`_`、`-`，前端当前实现通常以 `submit_` 前缀生成

### 6.2 提交前预检查

`POST /api/v1/agents/precheck`

#### 6.2.1 用途

- 校验当前提交参数是否合法
- 返回非阻断性警告信息
- 不创建评测任务

#### 6.2.2 成功响应

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "ok": true,
    "warnings": [
      "该次结果将进入公开排行榜，请确认描述中不包含敏感信息。",
      "当前超时时间高于建议值 20 分钟，评测排队与执行耗时可能更长。"
    ]
  }
}
```

#### 6.2.3 与 submit 的关系

- `precheck` 与 `submit` 使用**完全一致**的请求体
- `precheck` 与 `submit` 使用**同一个** `requestId`
- `precheck` 不会创建任务，也不会返回 `evaluationId`
- 前端无论 `warnings` 是否为空，都会弹出确认窗口

#### 6.2.4 常见失败响应

```json
{
  "code": 40001,
  "message": "API 地址格式不合法：baseUrl 必须以 http:// 或 https:// 开头。",
  "data": null
}
```

```json
{
  "code": 40002,
  "message": "参数 difficulty 必须在 0 到 1 之间，步长为 0.1。",
  "data": null
}
```

```json
{
  "code": 40003,
  "message": "至少需要选择一个数据集。",
  "data": null
}
```

```json
{
  "code": 40004,
  "message": "数据集 A999 不存在或已下线，无法选择。",
  "data": null
}
```

```json
{
  "code": 40005,
  "message": "Docker 提交方式当前不可用，请切换为 API 方式。",
  "data": null
}
```

### 6.3 正式提交

`POST /api/v1/agents/submit`

#### 6.3.1 用途

- 创建评测任务
- 返回 `evaluationId`
- 供前端跳转到评测详情页

#### 6.3.2 成功响应

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "evaluationId": "eval_1711960000123",
    "status": "pending",
    "createdAt": "2026-04-01T12:00:00Z"
  }
}
```

#### 6.3.3 提交自包含原则

`submit` 不应优化为“只传 `requestId`”。

**正式结论**：`submit` 必须继续提交完整请求体，并在服务端再次校验。

原因如下：

- `submit` 是真正创建任务的确认动作，必须是自包含、可重放、可审计的请求
- 如果 `submit` 只传 `requestId`，后端就必须保存 `precheck` 时的请求体快照
- 这会让本来可以保持无状态的提交接口，变成依赖临时服务端状态的接口
- 一旦遇到多实例部署、服务重启、缓存过期、跨标签页操作、长时间停留后再确认等场景，复杂度会明显上升
- 传完整请求体的成本，只是多传一次小体积 JSON，远低于引入临时缓存和一致性恢复机制的成本

#### 6.3.4 submit 为什么仍要再次校验

- 防御跳过 `precheck` 的客户端
- 防御 `precheck` 之后参数被篡改
- 让后端可以把最终生效的提交参数快照直接入库
- 让幂等冲突时可以基于完整 payload 准确返回 `40900`

#### 6.3.5 requestId 与 submit 的关系

- `submit` 与 `precheck` 使用同一 `requestId`
- 同一用户 + 同一 `requestId` 的重复提交，后端必须返回同一 `evaluationId`
- 若同一 `requestId` 对应的关键业务参数不一致，后端应返回 `40900`

#### 6.3.6 常见失败响应

```json
{
  "code": 40900,
  "message": "相同的 requestId 已提交过，但参数不一致。请生成新的 requestId 重新提交。",
  "data": null
}
```

```json
{
  "code": 50000,
  "message": "创建评测任务失败，服务暂时不可用。",
  "data": null
}
```

#### 6.3.7 前端成功后行为

- 清空提交草稿
- 清空 `pendingRequest`
- 跳转到 `/user/evaluation/{evaluationId}`

## 7. 前端校验、适配与本地持久化

### 7.1 提交方式与字段联动

- `submitMethod=api`
  - 必须提供 `api.baseUrl`
  - `api.baseUrl` 必须为合法 `http/https` URL
  - `docker` 必须为 `null`
- `submitMethod=docker`
  - 必须提供 `docker.imageUri`
  - `api` 必须为 `null`

### 7.2 必填项与数量约束

前端提交前应阻断以下非法输入：

- 智能体名称为空
- 智能体名称长度超出 `1-100`
- 未选择提交方式
- API 模式下未填写 `baseUrl`
- Docker 模式下未填写 `imageUri`
- `datasetIds` 为空
- `datasetIds` 数量超过 `100`
- `datasetIds` 有重复项
- `difficulty` 或 `timeoutMinutes` 超出元数据范围

### 7.3 数据集字段映射

前端内部状态使用：

```json
{
  "selectedDatasetIds": ["A1", "B1"]
}
```

真正发给后端前，必须转换成：

```json
{
  "datasetIds": ["A1", "B1"]
}
```

正式接口契约只使用 `datasetIds`；前端不得把 `selectedDatasetIds` 作为接口字段透传给后端。

### 7.4 本地持久化边界

提交页会持久化以下非敏感字段：

- `submitMethod`
- `agentName`
- `description`
- `api.baseUrl`
- `docker.imageUri`
- `docker.username`
- `parameters`
- `publicToLeaderboard`
- `selectedDatasetIds`
- `expandedCategoryIds`

### 7.5 pendingRequest 概念

除草稿字段外，前端还应持久化一个独立的 `pendingRequest` 对象，用于幂等重试：

```json
{
  "pendingRequest": {
    "requestId": "8c5ecb4e-79f9-47eb-84d8-a8aa0d53f27f",
    "payloadDigest": "{\"agentName\":\"安全卫士 v1.0\",\"submitMethod\":\"api\",\"datasetIds\":[\"A1\",\"B1\"]}",
    "createdAt": "2026-04-03T10:00:00Z"
  }
}
```

其语义如下：

- `requestId`：当前这次提交意图的幂等键
- `payloadDigest`：规范化后的稳定字符串摘要
- `createdAt`：本次幂等键首次生成时间

失效规则：

- 关键业务字段变化导致 `payloadDigest` 改变时，旧 `pendingRequest` 失效
- `submit` 成功后，`pendingRequest` 清除
- 用户手动重置表单时，`pendingRequest` 清除

### 7.6 敏感字段不持久化

以下字段不应持久化到本地存储：

- `api.token`
- `docker.password`
- 其他敏感凭证

## 8. 推荐错误码与前端处理

| code    | HTTP 状态 | API 位置                                       | 含义                              | 前端处理建议                        |
| ------- | --------- | ---------------------------------------------- | --------------------------------- | ----------------------------------- |
| `0`     | 200       | 所有                                           | 成功                              | 无特殊处理                          |
| `40001` | 400       | `precheck`、`submit`                           | API 地址格式错误                  | 显示 `message`，提示检查 `baseUrl`  |
| `40002` | 400       | `submit-meta`、`catalog`、`precheck`、`submit` | 参数超出范围                      | 提示用户调整参数                    |
| `40003` | 400       | `precheck`、`submit`                           | 未选择任何数据集                  | 提示用户勾选数据集                  |
| `40004` | 400       | `precheck`、`submit`                           | 数据集不存在、已下线或不可选      | 提示用户刷新目录并重新选择          |
| `40005` | 400       | `precheck`、`submit`                           | 提交方式当前不可用                | 提示用户切换提交方式                |
| `40100` | 401       | `precheck`、`submit`                           | 未登录或登录失效                  | 触发未授权处理，要求重新登录        |
| `40400` | 404       | `datasets/{id}`                                | 数据集不存在                      | 数据集详情页展示“数据集不存在”      |
| `40900` | 409       | `submit`                                       | 同一 `requestId` 但关键参数不一致 | 提示重新生成 `requestId` 并再次提交 |
| `50000` | 500       | 所有                                           | 服务器内部错误                    | 显示“服务异常，请稍后重试”          |

## 9. 性能与扩展性考量

### 9.1 数据集目录缓存

- 前端通过 `catalogVersion` 检测版本变化
- 若目录版本变化，前端会保留仍有效的数据集选择并提示用户
- 建议后端为目录接口设置合理缓存头

### 9.2 提交接口幂等实现

- 建议后端将 `(user_id, request_id)` 作为唯一键
- `submit` 不依赖 `precheck` 阶段的服务端缓存
- 重试逻辑只依赖正式入库的幂等记录

### 9.3 参数快照审计

建议后端在成功创建任务时，把规范化后的完整提交参数快照入库，包括：

- 业务字段
- `requestId`
- `createdAt`
- 当前用户标识

## 10. 联调建议顺序

1. `GET /api/v1/datasets/catalog`
2. `GET /api/v1/datasets/{datasetId}`
3. `GET /api/v1/agents/submit-meta`
4. `POST /api/v1/agents/precheck`
5. `POST /api/v1/agents/submit`
6. 评测相关接口见 `share/evaluations接口.md`

## 附录 A：核心 TypeScript 类型

### A.1 提交元数据

```typescript
interface SubmitMetaResponse {
  supportedMethods: ("api" | "docker")[];
  difficulty: RangeMetadata;
  timeoutMinutes: RangeMetadata & { recommendedMax: number };
  retryEnabled: { default: boolean };
  publicToLeaderboard: { default: boolean };
}

interface RangeMetadata {
  min: number;
  max: number;
  step: number;
  default: number;
}
```

### A.2 提交请求体

```typescript
interface SubmitAgentPayload {
  agentName: string;
  description?: string;
  submitMethod: "api" | "docker";
  api?: {
    baseUrl: string;
    token?: string;
  } | null;
  docker?: {
    imageUri: string;
    username?: string;
    password?: string;
  } | null;
  parameters: {
    difficulty: number;
    timeoutMinutes: number;
    retryEnabled: boolean;
  };
  publicToLeaderboard: boolean;
  datasetIds: string[];
  requestId: string;
}
```

### A.3 预检查与正式提交响应

```typescript
interface PrecheckResponse {
  ok: boolean;
  warnings: string[];
}

interface SubmitResponse {
  evaluationId: string;
  status: "pending";
  createdAt: string;
}
```
