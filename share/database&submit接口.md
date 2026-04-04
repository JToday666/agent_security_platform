# 数据集与提交接口

## 1. 文档目标

本文档定义当前前端在“数据集目录 / 数据集详情 / 智能体提交”场景下已经固定的接口契约。
`backend/` 当前尚未完整落地本文涉及的 `datasets / agents / evaluations` 接口，因此本文以 **前端现有类型、服务层和页面行为** 为准，用于后续后端实现和联调对齐。

本文覆盖：

- `GET /api/v1/datasets/catalog`
- `GET /api/v1/datasets/{datasetId}`
- `GET /api/v1/agents/submit-meta`
- `POST /api/v1/agents/precheck`
- `POST /api/v1/agents/submit`

评测记录、评测详情与任务控制接口见 [evaluations接口.md](./evaluations接口.md)。

## 2. 页面与调用时机

### 2.1 数据集列表页 `/dataset`

- 页面挂载时调用 `GET /api/v1/datasets/catalog`
- 用户点击某个数据集后跳转到 `/dataset/{datasetId}`
- 详情页根据路由参数调用 `GET /api/v1/datasets/{datasetId}`

### 2.2 提交页 `/user/submit`

- 页面初始化时调用 `GET /api/v1/agents/submit-meta`
- 页面初始化时调用一次 `GET /api/v1/datasets/catalog`
- 本地恢复草稿后，会用 catalog 对已选数据集和展开分组做一次同步清理
- 用户点击“提交任务”时，前端先做本地校验，再调用 `POST /api/v1/agents/precheck`
- 用户确认后，再调用 `POST /api/v1/agents/submit`
- 提交成功后跳转到 `/user/evaluation/{evaluationId}`

关键约定：

- catalog 不再接收 `difficulty` 参数
- 提交页后续调整 `difficulty` 时，前端不再重新请求 catalog
- 目录区域仅在初始化和用户手动重试时请求 catalog
- `difficulty` 仍保留在 `precheck` 与 `submit` 的 `parameters.difficulty` 中

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
  "code": 40002,
  "message": "参数校验失败。",
  "data": null
}
```

前端依赖规则：

- `code === 0` 表示成功
- `code !== 0` 表示业务失败
- 失败时前端优先展示 `message`
- 失败时前端只保证读取 `code` 与 `message`
- 失败时 `data` 可以为 `null`，也可以是便于排查的占位结构

### 3.3 鉴权要求

| 接口                               | 是否需要登录 | 说明                   |
| ---------------------------------- | ------------ | ---------------------- |
| `GET /api/v1/datasets/catalog`     | 否           | 公共目录页与提交页共用 |
| `GET /api/v1/datasets/{datasetId}` | 否           | 公共数据集详情页       |
| `GET /api/v1/agents/submit-meta`   | 否           | 提交页初始化元数据     |
| `POST /api/v1/agents/precheck`     | 是           | 提交前预检查           |
| `POST /api/v1/agents/submit`       | 是           | 正式创建评测任务       |

### 3.4 前端显示规则

- `datasetId` / `datasetIds` 是内部标识，只用于路由、缓存、勾选状态和接口传参
- 用户界面统一显示 `name`
- 不向用户直接暴露 `A1 / C2` 这类内部数据集代码
- 当前端未拿到可直接展示的名称时，会尝试使用前端内置 taxonomy 回填公开名称
- 若仍无法解析，则退化为通用占位文案，而不是直接显示内部代码

## 4. 数据集接口

### 4.1 获取数据集目录

**接口**

`GET /api/v1/datasets/catalog`

**用途与调用时机**

- 数据集列表页初始化使用
- 提交页初始化与手动重试使用

**是否需要登录**

- 否

**Query 参数**

- 无

**请求示例**

```http
GET /api/v1/datasets/catalog HTTP/1.1
Host: example.com
```

**成功响应示例**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "catalogVersion": "2026-04-01T10:00:00Z",
    "categoryCount": 7,
    "subcategoryCount": 32,
    "categories": [
      {
        "categoryId": "confidentiality",
        "name": "机密性",
        "meaning": "敏感信息保护与最小暴露",
        "description": "聚焦隐私、凭证与业务机密等敏感信息在对话、检索与工具链中的最小暴露要求。",
        "sort": 1,
        "enabled": true,
        "subcategoryCount": 6,
        "subcategories": [
          {
            "datasetId": "A1",
            "name": "身份信息泄露",
            "shortDescription": "评估模型在身份字段核验、回显与引用过程中的泄露风险。",
            "sampleCount": 960,
            "updatedAt": "2026-04-01T10:00:00Z",
            "enabled": true
          },
          {
            "datasetId": "A2",
            "name": "凭证信息暴露",
            "shortDescription": "评估模型对令牌、密钥和密码等高敏信息的保护能力。",
            "sampleCount": 812,
            "updatedAt": "2026-04-01T10:00:00Z",
            "enabled": true
          }
        ]
      }
    ]
  }
}
```

**失败响应示例**

```json
{
  "code": 50000,
  "message": "目录加载失败，请稍后重试。",
  "data": null
}
```

**字段与契约说明**

- `catalogVersion` 用于草稿同步、已选数据集失效清理和目录更新提示
- `categoryCount` 与 `subcategoryCount` 基于本次返回结果统计
- `categories[].subcategories` 仅包含当前可供前端展示和选择的评测项
- catalog 不接收 `difficulty` query 参数
- 后端返回的是完整可用目录，而不是按 `difficulty` 裁剪后的子集
- 若某个大类下没有可用子项，可以不返回该大类

### 4.2 获取单个数据集详情

**接口**

`GET /api/v1/datasets/{datasetId}`

**用途与调用时机**

- 数据集详情页根据路由参数加载

**是否需要登录**

- 否

**Path 参数**

| 字段        | 类型   | 必填 | 说明           |
| ----------- | ------ | ---- | -------------- |
| `datasetId` | string | 是   | 数据集内部标识 |

**请求示例**

```http
GET /api/v1/datasets/A1 HTTP/1.1
Host: example.com
```

**成功响应示例**

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
      "meaning": "敏感信息保护与最小暴露"
    },
    "shortDescription": "评估模型在身份字段核验、回显与引用过程中的泄露风险。",
    "fullDescription": "该数据集重点覆盖真实身份、伪造身份、越权查询与工具结果泄露等场景。",
    "sampleCount": 960,
    "updatedAt": "2026-04-01T10:00:00Z",
    "highlights": [
      "覆盖高频身份查询与诱导泄露路径",
      "包含工具调用回显和多轮追问样本"
    ],
    "scenarios": [
      "攻击者诱导系统披露个人身份信息",
      "攻击者通过工具链结果回显获取敏感字段"
    ],
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

**失败响应示例：数据集不存在**

```json
{
  "code": 40400,
  "message": "评测项不存在。",
  "data": null
}
```

**失败响应示例：详情加载失败**

```json
{
  "code": 50000,
  "message": "详情加载失败，请重试。",
  "data": null
}
```

**字段与契约说明**

- `datasetId` 必须与 catalog 中同一数据集保持一致
- `name` 是用户界面的主展示名称
- `resources` 与 `media` 即使为空，也建议返回空数组而不是省略字段
- `category.name` 与 `category.meaning` 会直接用于详情页展示

## 5. 提交元数据接口

### 5.1 获取提交页元数据

**接口**

`GET /api/v1/agents/submit-meta`

**用途与调用时机**

- 提交页初始化加载参数范围、默认值和提交方式

**是否需要登录**

- 否

**请求示例**

```http
GET /api/v1/agents/submit-meta HTTP/1.1
Host: example.com
```

**成功响应示例**

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

**失败响应示例**

```json
{
  "code": 50000,
  "message": "提交配置加载失败，请稍后重试。",
  "data": null
}
```

**字段与契约说明**

- 前端只接受当前扁平结构，不兼容旧的 `parameterMeta` 包裹形式
- `difficulty` 仍是提交参数的重要组成部分，即使它不再参与 catalog 请求
- `timeoutMinutes.recommendedMax` 用于前端展示软性提示，不影响合法范围判断

## 6. 提交接口

### 6.1 `precheck` 与 `submit` 共用请求体

`POST /api/v1/agents/precheck` 与 `POST /api/v1/agents/submit` 使用同一请求体结构。

前端内部字段是 `selectedDatasetIds`，发送给后端前统一适配为 `datasetIds`。

**Body 字段**

| 字段                  | 类型     | 必填 | 说明                              |
| --------------------- | -------- | ---- | --------------------------------- |
| `agentName`           | string   | 是   | 智能体名称，前端限制最长 100 字符 |
| `description`         | string   | 否   | 智能体描述                        |
| `submitMethod`        | string   | 是   | `api` 或 `docker`                 |
| `api`                 | object   | 条件 | `submitMethod=api` 时必填         |
| `docker`              | object   | 条件 | `submitMethod=docker` 时必填      |
| `parameters`          | object   | 是   | 运行参数                          |
| `publicToLeaderboard` | boolean  | 是   | 是否公开到排行榜                  |
| `datasetIds`          | string[] | 是   | 最终需要运行的数据集 ID 列表      |
| `requestId`           | string   | 是   | 单次正式提交的幂等键              |

**API 模式请求体示例**

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
    "timeoutMinutes": 18,
    "retryEnabled": false
  },
  "publicToLeaderboard": true,
  "datasetIds": ["A1", "B1", "D1"],
  "requestId": "submit_20260404_xxxxx"
}
```

**Docker 模式请求体示例**

```json
{
  "agentName": "安全卫士 Docker 版",
  "description": "使用镜像部署的评测智能体。",
  "submitMethod": "docker",
  "api": null,
  "docker": {
    "imageUri": "registry.example.com/agents/security-guardian:1.0.0",
    "username": "ci-bot",
    "password": "******"
  },
  "parameters": {
    "difficulty": 0.6,
    "timeoutMinutes": 20,
    "retryEnabled": true
  },
  "publicToLeaderboard": false,
  "datasetIds": ["A1", "C2", "F1"],
  "requestId": "submit_20260404_docker001"
}
```

**互斥规则**

- `submitMethod === "api"` 时，`api` 必填，`docker` 必须为 `null`
- `submitMethod === "docker"` 时，`docker` 必填，`api` 必须为 `null`
- `datasetIds` 表示最终要运行的数据集集合，不代表用户界面上的分类结构
- `requestId` 用作正式提交幂等键，格式需满足前端校验规则

### 6.2 提交前预检查

**接口**

`POST /api/v1/agents/precheck`

**用途与调用时机**

- 用户点击“提交任务”后、正式提交前调用
- 用于参数和选择项预校验，以及给出非阻塞警告

**是否需要登录**

- 是

**成功响应示例**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "ok": true,
    "warnings": [
      "本次结果将进入公开排行榜，请确认描述中不包含敏感信息。",
      "当前超时时间高于建议值 20，评测排队与执行耗时可能更长。"
    ]
  }
}
```

**失败响应示例：参数校验失败**

```json
{
  "code": 40002,
  "message": "请至少选择一个评测项",
  "data": {
    "ok": false,
    "warnings": ["请至少选择一个评测项"]
  }
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

**字段与契约说明**

- `precheck` 必须是无副作用校验，不创建任务、不消费 `requestId`
- 当前前端只依赖 `ok` 与 `warnings`
- 当前前端可感知的校验失败场景包括：
  - 智能体名称为空或超长
  - API 地址非法
  - Docker 镜像地址为空
  - `difficulty` 或 `timeoutMinutes` 越界
  - 未选择数据集
  - 选择了重复或失效数据集
  - `requestId` 格式不合法

### 6.3 正式提交

**接口**

`POST /api/v1/agents/submit`

**用途与调用时机**

- 用户通过 `precheck` 并确认后调用
- 正式创建评测任务

**是否需要登录**

- 是

**成功响应示例**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "evaluationId": "eval_20260404_001",
    "status": "pending",
    "createdAt": "2026-04-04T10:30:00Z"
  }
}
```

**失败响应示例：参数校验失败**

```json
{
  "code": 40002,
  "message": "requestId 格式不正确，请重试。",
  "data": null
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

**字段与契约说明**

- 同一 `requestId` 的重复正式提交，应返回同一任务结果或等价结果，避免重复建单
- 前端收到 `evaluationId` 后会立即跳转到 `/user/evaluation/{evaluationId}`
- `status` 当前前端按 `EvaluationStatus` 解析，提交成功后通常为 `pending`

## 7. 推荐错误码

| code    | HTTP | 场景                  | 含义                       |
| ------- | ---- | --------------------- | -------------------------- |
| `0`     | 200  | 全部接口              | 成功                       |
| `40002` | 400  | `precheck` / `submit` | 参数校验失败               |
| `40100` | 401  | 需要登录的提交接口    | 未登录或登录失效           |
| `40400` | 404  | `GET /datasets/{id}`  | 数据集不存在               |
| `50000` | 500  | 全部接口              | 服务内部错误或上游加载失败 |

## 8. 提交调用流程图

```mermaid
flowchart TD
    A[进入提交页 /user/submit] --> B[请求 submit-meta]
    A --> C[请求 datasets/catalog]
    C --> D[恢复本地草稿并按 catalog 清理失效数据]
    D --> E[用户编辑表单与勾选数据集]
    E --> F[本地校验]
    F -->|失败| G[展示本地错误并阻止提交]
    F -->|通过| H[调用 agents/precheck]
    H -->|失败| I[展示 message]
    H -->|成功| J[展示 warnings 并等待用户确认]
    J --> K[调用 agents/submit]
    K -->|失败| L[展示 message]
    K -->|成功| M[跳转 /user/evaluation/{evaluationId}]
```

## 9. 后续推荐优化

以下内容仅为推荐方向，不代表后端已实现：

- `precheck` 可扩展返回标准化摘要，例如提交方式、公开性、最终数据集数量与高风险提示，减少前端确认弹窗的本地拼装逻辑
- `submit` 可扩展返回首屏可用的 evaluation snapshot，而不是只返回 `evaluationId`
- `submit-meta` 若后续出现更复杂约束，可增加独立的文档化辅助字段，但应保持向后兼容
