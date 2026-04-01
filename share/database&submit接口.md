# database&submit接口

## 1. 文档目标

本文档面向后端开发，描述当前前端在“数据集”和“提交智能体”相关页面上已经固定下来的接口交互契约。

本文档只以当前 `frontend` 代码的真实依赖为准，不以 `backend` 当前实现为准。当前后端只实现了登录相关接口，因此以下接口均视为待开发接口。

本次文档覆盖完整提交流程涉及的全部接口：

- `GET /api/v1/agents/submit-meta`
- `GET /api/v1/datasets/catalog`
- `GET /api/v1/datasets/{datasetId}`
- `POST /api/v1/agents/precheck`
- `POST /api/v1/agents/submit`
- `GET /api/v1/evaluations`
- `GET /api/v1/evaluations/{evaluationId}`

## 2. 关联页面与调用时机

### 2.1 数据集相关页面

- 数据集列表页：`/dataset`
  - 页面挂载时调用 `GET /api/v1/datasets/catalog`
  - 当前列表页不传 `difficulty`
- 数据集详情页：`/dataset/:datasetId`
  - 页面挂载时调用 `GET /api/v1/datasets/{datasetId}`
  - 当路由参数 `datasetId` 变化时重新调用
  - 若接口返回 `40400`，前端显示“数据集不存在”
  - 若接口返回其他错误或请求失败，前端显示“详情加载失败”，并保留重试按钮

### 2.2 提交智能体相关页面

- 提交页：`/user/submit`
  - 页面初始化时先调用 `GET /api/v1/agents/submit-meta`
  - 获取到参数元数据后，再按当前难度调用 `GET /api/v1/datasets/catalog?difficulty=...`
  - 提交前先调用 `POST /api/v1/agents/precheck`
  - 预检查成功后再调用 `POST /api/v1/agents/submit`
  - 提交成功后跳转 `/user/evaluation/{evaluationId}`
- 用户中心评测记录页：`/user`
  - 页面挂载时调用 `GET /api/v1/evaluations`
- 评测详情页：`/user/evaluation/:evaluationId`
  - 页面挂载时调用 `GET /api/v1/evaluations/{evaluationId}`

## 3. 通用约定

### 3.1 Base URL

前端请求层 `frontend/src/utils/request.ts` 默认使用：

```text
/api/v1
```

下面所有接口路径都基于该前缀。

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

当前前端同时兼容两种错误形式：

- HTTP 200 + envelope 中 `code != 0`
- HTTP 非 2xx，响应体中仍带 `message` 或 `detail`

但从前端消费角度，更推荐后端统一返回 envelope，并在鉴权失败时使用 HTTP 401。

### 3.4 鉴权要求

| 接口                                     | 是否需要登录 | 说明                     |
| ---------------------------------------- | ------------ | ------------------------ |
| `GET /api/v1/agents/submit-meta`         | 否           | 提交页初始化依赖         |
| `GET /api/v1/datasets/catalog`           | 否           | 数据集列表、提交页都依赖 |
| `GET /api/v1/datasets/{datasetId}`       | 否           | 数据集详情页依赖         |
| `POST /api/v1/agents/precheck`           | 是           | 提交流程中的预检查       |
| `POST /api/v1/agents/submit`             | 是           | 正式创建评测任务         |
| `GET /api/v1/evaluations`                | 是           | 当前登录用户的评测记录   |
| `GET /api/v1/evaluations/{evaluationId}` | 是           | 当前登录用户的评测详情   |

401 时前端行为如下：

- 清理登录态
- 弹出登录框
- 记录当前目标路由
- 登录成功后自动跳回之前目标页面

### 3.5 幂等约定

`POST /api/v1/agents/submit` 必须支持幂等。

当前前端每次提交都会携带 `requestId`，语义如下：

- 同一用户 + 同一 `requestId` 的重复提交，后端应返回同一条评测任务
- 不应重复创建任务
- 若同一 `requestId` 对应的关键业务参数与首次提交不一致，建议返回 `40900`

## 4. 数据集接口

### 4.1 获取数据集目录

`GET /api/v1/datasets/catalog`

#### 4.1.1 用途

- 数据集列表页展示全部目录
- 提交页按当前攻击难度刷新“当前可用数据集”

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
        "categoryId": "confidentiality",
        "name": "机密性",
        "meaning": "防止信息泄露",
        "description": "覆盖身份、密钥、隐私等高敏感信息的泄露风险。",
        "sort": 1,
        "enabled": true,
        "subcategoryCount": 2,
        "subcategories": [
          {
            "datasetId": "A1",
            "name": "身份信息泄露",
            "shortDescription": "测试多轮追问和绕行提示下的身份字段泄露。",
            "sampleCount": 1280,
            "updatedAt": "2026-03-28T12:00:00Z",
            "enabled": true
          }
        ]
      }
    ]
  }
}
```

#### 4.1.4 字段说明

- `catalogVersion`
  - 目录版本号
  - 提交页会将其与本地草稿持久化状态联动，用于提示目录是否发生变化
- `categoryCount`
  - 当前返回结果中的大类总数
- `subcategoryCount`
  - 当前返回结果中的数据集总数
- `categories`
  - 数据集大类列表
- `categories[].subcategories`
  - 当前前端沿用历史字段名，实际承载“数据集摘要列表”
- `enabled`
  - 前端会基于该字段做“可用项”过滤，建议后端直接只返回可用项

#### 4.1.5 难度筛选规则

当前前端对该接口有两种使用方式：

- 数据集列表页：不传 `difficulty`
- 提交页：传 `difficulty`

后端建议行为：

- 不传 `difficulty` 时返回完整目录
- 传 `difficulty` 时返回该难度下可用的数据集子集
- 若某个大类在该难度下没有任何数据集，应从结果中移除该大类
- `categoryCount` 和 `subcategoryCount` 必须基于过滤后结果重新计算
- 若过滤后无数据，返回成功响应，`categories` 为空数组

筛空示例：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "catalogVersion": "2026-04-01T10:00:00Z",
    "categoryCount": 0,
    "subcategoryCount": 0,
    "categories": []
  }
}
```

#### 4.1.6 失败语义

- `40002`：`difficulty` 非法、越界、步长不合法
- `50000`：服务内部错误

前端不希望后端对非法难度值静默纠正或自动四舍五入，因为这会导致前端误以为用户输入生效。

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
      "categoryId": "confidentiality",
      "name": "机密性",
      "meaning": "防止信息泄露"
    },
    "shortDescription": "测试多轮追问和绕行提示下的身份字段泄露。",
    "fullDescription": "该数据集围绕身份证号、手机号、地址、邮箱等高敏感字段构造多轮攻击样本，用于验证智能体是否会在追问、伪装授权和历史会话回放中回显真实信息。",
    "sampleCount": 1280,
    "updatedAt": "2026-03-28T12:00:00Z",
    "highlights": [
      "覆盖直接索取、间接诱导和历史会话挖掘。",
      "适合验证脱敏、拒答和重写策略。"
    ],
    "scenarios": ["客服场景下回显用户手机号。", "知识助手回显员工实名与邮箱。"],
    "resources": [
      {
        "label": "查看字段说明",
        "url": "https://example.com/docs/datasets/A1",
        "type": "docs"
      }
    ],
    "media": [
      {
        "mediaId": "A1-image",
        "type": "image",
        "title": "身份信息泄露样例概览",
        "description": "用于展示典型攻击样本与响应结构。",
        "url": "https://cdn.example.com/datasets/A1/overview.png",
        "coverUrl": null,
        "sort": 1
      }
    ]
  }
}
```

#### 4.2.3 字段说明

- `category`
  - 数据集所属分类摘要
- `highlights`
  - 数据集评测重点，页面按列表展示
- `scenarios`
  - 典型使用或攻击场景，页面按列表展示
- `resources`
  - 当前前端类型已接入该字段，虽然详情页当前未渲染，但正式接口仍应返回
- `resources[].type`
  - 当前约定值：`docs`、`download`、`demo`
- `media`
  - 媒体资源列表，详情页使用 `DatasetMediaGallery` 展示
- `media[].type`
  - 当前约定值：`image`、`video`
- `media[].coverUrl`
  - 视频封面，可为 `null`
- `media[].sort`
  - 可选排序字段

#### 4.2.4 一致性要求

- `datasetId`、`name`、`shortDescription`、`sampleCount`、`updatedAt` 应与目录接口中的同一数据集保持一致
- 目录与详情应来自同一份主数据源，避免出现名称或统计不一致

#### 4.2.5 失败语义

- `40400`：数据集不存在、已下线或当前不可访问
- `50000`：服务内部错误

前端页面处理规则：

- `40400` 显示“不存在”状态
- 非 `40400` 显示“加载失败”状态
- 都会保留重试能力

## 5. 提交前元数据接口

### 5.1 获取提交参数元数据

`GET /api/v1/agents/submit-meta`

#### 5.1.1 用途

- 决定提交页支持哪些提交方式
- 决定攻击难度、超时时间、布尔参数的默认值与取值范围
- 决定前端对超时时间的软提示阈值

#### 5.1.2 成功响应

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

#### 5.1.3 字段说明

- `supportedMethods`
  - 当前前端只支持 `api` 和 `docker`
- `difficulty`
  - 攻击难度元数据
- `timeoutMinutes`
  - 单次评测超时元数据
- `timeoutMinutes.recommendedMax`
  - 软提示阈值，不是硬上限
  - 当前前端当 `timeoutMinutes > recommendedMax` 时，会在预检查阶段提示执行耗时可能更长
- `retryEnabled.default`
  - 失败重试默认值
- `publicToLeaderboard.default`
  - 是否公开到排行榜默认值

#### 5.1.4 兼容说明

前端当前仍兼容旧结构：

```json
{
  "supportedMethods": ["api", "docker"],
  "parameterMeta": {
    "difficulty": { "min": 0, "max": 1, "step": 0.1, "default": 0.5 },
    "timeoutMinutes": { "min": 15, "max": 30, "step": 1, "default": 15 },
    "retryEnabled": { "default": false },
    "publicToLeaderboard": { "default": true }
  }
}
```

但这只是过渡兼容层。后端新实现建议直接返回扁平结构，不再使用 `parameterMeta` 包裹。

#### 5.1.5 失败语义

- `50000`：服务内部错误

该接口失败时，提交页会直接进入“页面初始化失败”状态。

## 6. 提交接口

### 6.1 提交前预检查

`POST /api/v1/agents/precheck`

#### 6.1.1 用途

- 校验当前提交参数是否合法
- 返回非阻断性告警信息
- 不创建评测任务

#### 6.1.2 请求体

前端页面内部字段名为 `selectedDatasetIds`，但发给后端前会在适配器层转换为 `datasetIds`。

推荐请求体如下：

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

#### 6.1.3 字段说明

- `agentName`
  - 必填，智能体名称
- `description`
  - 选填，智能体描述
- `submitMethod`
  - 当前仅支持 `api`、`docker`
- `api`
  - 当 `submitMethod=api` 时使用
- `api.baseUrl`
  - 必填，且必须为合法 `http/https` URL
- `api.token`
  - 选填，敏感字段，前端不会持久化
- `docker`
  - 当 `submitMethod=docker` 时使用
- `docker.imageUri`
  - 必填
- `docker.username`
  - 选填
- `docker.password`
  - 选填，敏感字段，前端不会持久化
- `parameters.difficulty`
  - 必须满足 `submit-meta.difficulty`
- `parameters.timeoutMinutes`
  - 必须满足 `submit-meta.timeoutMinutes`
- `parameters.retryEnabled`
  - 布尔值
- `publicToLeaderboard`
  - 布尔值
- `datasetIds`
  - 至少一个，且必须都是当前有效数据集
- `requestId`
  - 幂等请求标识，正式提交时也会复用

#### 6.1.4 成功响应

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "ok": true,
    "warnings": [
      "该次结果将进入公开排行榜，请确认描述中不包含敏感信息。",
      "当前超时时间高于建议值 20，评测排队与执行耗时可能更长。"
    ]
  }
}
```

#### 6.1.5 交互语义

- `warnings` 为非阻断提示
- 前端会先展示这些提示，再继续正式提交
- 若预检查失败，前端不会继续调用正式提交接口

#### 6.1.6 建议错误语义

- `40001`：API 地址格式错误
- `40002`：参数超出允许范围
- `40003`：未选择任何数据集
- `40004`：数据集不存在、已下线或当前不可选
- `40005`：提交方式当前不可用
- `40100`：未登录或登录失效
- `50000`：服务内部错误

### 6.2 正式提交

`POST /api/v1/agents/submit`

#### 6.2.1 用途

- 创建评测任务
- 返回任务 ID，供前端跳转评测详情页

#### 6.2.2 请求体

与 `POST /api/v1/agents/precheck` 保持一致。

#### 6.2.3 成功响应

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

#### 6.2.4 字段说明

- `evaluationId`
  - 评测任务唯一标识
- `status`
  - 当前前端支持值：`pending`、`running`、`completed`
- `createdAt`
  - ISO 8601 时间字符串

#### 6.2.5 前端成功后行为

- 清空本地提交草稿
- 跳转到 `/user/evaluation/{evaluationId}`

#### 6.2.6 幂等要求

- 同一用户 + 同一 `requestId` 的重复提交，必须返回同一 `evaluationId`
- 不应重复创建任务
- 如果同一 `requestId` 对应不同的关键业务参数，建议返回 `40900`

## 7. 评测记录接口

### 7.1 获取当前用户评测记录

`GET /api/v1/evaluations`

#### 7.1.1 用途

- 用户中心 `/user` 页面展示评测记录列表

#### 7.1.2 成功响应

```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "evaluationId": "eval_20260331_001",
      "agentName": "安全卫士 v1.0",
      "description": "面向企业场景的多工具安全代理。",
      "createdAt": "2026-03-31T10:20:00Z",
      "updatedAt": "2026-03-31T11:05:00Z",
      "status": "completed",
      "publicToLeaderboard": true,
      "datasetIds": ["A1", "B1"],
      "datasetNames": ["身份信息泄露", "指令篡改"],
      "submitMethod": "api",
      "score": 94.6,
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

#### 7.1.3 字段说明

- `datasetNames`
  - 页面直接展示的人类可读名称列表
- `score`
  - 任务未完成时可为 `null` 或不返回
- `ownerName`
  - 当前任务所属用户的展示名

#### 7.1.4 排序建议

前端当前假定“最新创建的任务优先展示”。推荐后端按 `createdAt` 倒序返回。

#### 7.1.5 失败语义

- `40100`：未登录或登录失效
- `50000`：服务内部错误

### 7.2 获取单个评测详情

`GET /api/v1/evaluations/{evaluationId}`

#### 7.2.1 用途

- 评测详情页 `/user/evaluation/:evaluationId` 展示摘要、告警和详细指标

#### 7.2.2 成功响应

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "evaluationId": "eval_20260331_001",
    "agentName": "安全卫士 v1.0",
    "description": "面向企业场景的多工具安全代理。",
    "createdAt": "2026-03-31T10:20:00Z",
    "updatedAt": "2026-03-31T11:05:00Z",
    "status": "completed",
    "publicToLeaderboard": true,
    "datasetIds": ["A1", "B1"],
    "datasetNames": ["身份信息泄露", "指令篡改"],
    "submitMethod": "api",
    "score": 94.6,
    "ownerName": "张三",
    "parameters": {
      "difficulty": 0.5,
      "timeoutMinutes": 18,
      "retryEnabled": false
    },
    "summary": "本次评测共覆盖 2 个数据集，核心安全指标表现稳定，建议结合详细指标继续优化高风险边界。",
    "warnings": [],
    "metrics": [
      {
        "name": "攻击检测率",
        "value": "96%",
        "percentage": 96,
        "description": "识别恶意提示与异常工具响应的能力。"
      }
    ]
  }
}
```

#### 7.2.3 字段说明

- `summary`
  - 详情页摘要文案
- `warnings`
  - 风险提示列表
- `metrics`
  - 指标卡片列表
- `metrics[].percentage`
  - 进度条数值，前端预期范围 `0-100`

#### 7.2.4 失败语义

- `40100`：未登录或登录失效
- `40300`：无权查看该任务
- `40400`：评测任务不存在
- `50000`：服务内部错误

## 8. 前端校验与映射规则

### 8.1 提交方式与字段联动

- `submitMethod=api`
  - 必须提供 `api.baseUrl`
  - `api.baseUrl` 必须为合法 `http/https` URL
- `submitMethod=docker`
  - 必须提供 `docker.imageUri`

### 8.2 参数范围

当前前端默认值为：

- `difficulty`
  - `min=0`
  - `max=1`
  - `step=0.1`
  - `default=0.5`
- `timeoutMinutes`
  - `min=15`
  - `max=30`
  - `step=1`
  - `default=15`
  - `recommendedMax=20`
- `retryEnabled.default=false`
- `publicToLeaderboard.default=true`

### 8.3 数据集字段映射

前端内部表单状态使用：

```json
{
  "selectedDatasetIds": ["A1", "B1"]
}
```

真正发给后端前会转换成：

```json
{
  "datasetIds": ["A1", "B1"]
}
```

因此后端正式接口契约请直接使用 `datasetIds`，不要使用 `selectedDatasetIds`。

### 8.4 本地持久化边界

提交页会持久化非敏感字段，包括：

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

提交页不会持久化：

- `api.token`
- `docker.password`
- 其他敏感凭证字段

后端不能假设刷新页面后这些敏感字段仍然存在。

## 9. 推荐错误码

| code    | 含义                         |
| ------- | ---------------------------- |
| `40001` | API 地址格式错误             |
| `40002` | 参数超出允许范围             |
| `40003` | 未选择任何数据集             |
| `40004` | 数据集不存在、已下线或不可选 |
| `40005` | 提交方式当前不可用           |
| `40100` | 未登录或登录失效             |
| `40300` | 无权访问该资源               |
| `40400` | 资源不存在                   |
| `40900` | 幂等冲突或重复请求参数不一致 |
| `50000` | 服务器内部错误               |

## 10. 联调建议顺序

建议后端按以下顺序实现，便于前端逐步切换真实接口：

1. `GET /api/v1/agents/submit-meta`
2. `GET /api/v1/datasets/catalog`
3. `GET /api/v1/datasets/{datasetId}`
4. `POST /api/v1/agents/precheck`
5. `POST /api/v1/agents/submit`
6. `GET /api/v1/evaluations`
7. `GET /api/v1/evaluations/{evaluationId}`

如果只想先打通提交页，至少需要先完成前 5 项。
