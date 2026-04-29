# agent接口

## 2. 获取 Agent 模板

```http
GET /api/v1/agents/templates
```

### 作用

返回后端内置注册模板。模板用于前端预填表单，首期存放在后端 `templates.py`，不建模板表。

### 成功响应

```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "templateId": "http_submit_poll_basic",
      "name": "提交 + 轮询 Agent",
      "description": "适用于先提交任务，再通过运行 ID 轮询结果的 Agent。",
      "recommended": true,
      "sortOrder": 10,
      "level": "basic",
      "tags": ["推荐", "异步", "轮询"],
      "defaultConfig": {
        "invokeMode": "submit_poll",
        "connection": {
          "baseUrl": "",
          "invokePath": "/api/runs",
          "resultPathTemplate": "/api/runs/{externalRunId}",
          "requestTimeoutSeconds": 30,
          "pollIntervalSeconds": 2,
          "pollTimeoutSeconds": 300
        },
        "auth": {
          "type": "bearer",
          "config": {
            "token": ""
          }
        },
        "platformInputMapping": {
          "task": "task",
          "entryUrl": "entryUrl",
          "timeoutSeconds": "timeoutSeconds",
          "sampleId": "sampleId",
          "evaluationId": "evaluationId",
          "maxSteps": "maxSteps"
        },
        "taskRenderMode": "goal_only",
        "customRequestBody": {},
        "requestOptions": {
          "structuredOutput": {
            "supported": true,
            "fieldAlias": "outputSchema"
          }
        },
        "platformOutputMapping": {
          "externalRunId": "data.runId",
          "status": "data.status",
          "finalAnswer": "data.answer",
          "errorMessage": "data.error.message",
          "stepCount": "data.metrics.stepCount",
          "artifacts": "data.artifacts"
        },
        "terminalStatuses": ["completed", "failed", "timed_out"],
        "successStatuses": ["completed"]
      }
    }
  ]
}
```

### 字段说明

| 字段          | 作用                             |
| ------------- | -------------------------------- |
| templateId    | 模板唯一标识                     |
| name          | 展示名称                         |
| description   | 适用场景                         |
| recommended   | 是否推荐，用于默认选中和标签展示 |
| sortOrder     | 展示顺序                         |
| level         | basic / advanced                 |
| tags          | 前端标签                         |
| defaultConfig | Agent 创建表单默认值             |

### 失败响应

```json
{
  "code": 50000,
  "message": "Agent 模板加载失败。",
  "data": null
}
```

## 3. 创建 Agent

```http
POST /api/v1/agents
```

### 请求体示例

```json
{
  "templateId": "http_submit_poll_basic",
  "name": "Skyvern Agent",
  "description": "通过 Skyvern API 执行 Web 自动化任务",
  "invokeMode": "submit_poll",
  "connection": {
    "baseUrl": "https://api.agent.example.com",
    "invokePath": "/v1/run/tasks",
    "resultPathTemplate": "/v1/run/tasks/{externalRunId}",
    "requestTimeoutSeconds": 30,
    "pollIntervalSeconds": 2,
    "pollTimeoutSeconds": 300
  },
  "auth": {
    "type": "api_key_header",
    "config": {
      "headerName": "x-api-key",
      "secret": "sk-demo"
    }
  },
  "platformInputMapping": {
    "task": "prompt",
    "entryUrl": "url",
    "timeoutSeconds": "timeout_sec",
    "sampleId": "case_id",
    "evaluationId": "job_id",
    "maxSteps": "max_steps"
  },
  "taskRenderMode": "goal_only",
  "customRequestBody": {
    "engine": "skyvern-2.0",
    "proxy_location": "RESIDENTIAL",
    "run_with": "agent"
  },
  "requestOptions": {
    "structuredOutput": {
      "supported": true,
      "fieldAlias": "data_extraction_schema"
    }
  },
  "platformOutputMapping": {
    "externalRunId": "task_id",
    "status": "status",
    "finalAnswer": "result.answer",
    "errorMessage": "error.message",
    "stepCount": "metrics.step_count",
    "artifacts": "artifacts"
  },
  "terminalStatuses": ["completed", "failed", "timed_out"],
  "successStatuses": ["completed"]
}
```

### 字段说明

| 字段                  | 作用                        | 设计理由                     |
| --------------------- | --------------------------- | ---------------------------- |
| templateId            | 来源模板 ID                 | 便于统计模板效果，不参与运行 |
| name                  | Agent 名称                  | 列表、详情、评测记录展示     |
| description           | 描述                        | 帮助用户识别用途             |
| invokeMode            | sync_response / submit_poll | 决定后端调用方式             |
| connection            | 外部服务连接配置            | 后端按该配置发起请求         |
| auth                  | 鉴权配置                    | 保存凭据并生成请求 header    |
| platformInputMapping  | 平台字段到外部请求字段名    | 用户填写字段名，不填写值     |
| customRequestBody     | 固定字段名和值              | 每次请求原样合并             |
| platformOutputMapping | 平台字段到响应 JSON 路径    | 用户填写路径，不填写返回值   |
| terminalStatuses      | 外部终态集合                | 判断轮询是否结束             |
| successStatuses       | 外部成功态集合              | 判断外部任务是否生命周期成功 |

### 关键校验

```text
platformInputMapping.task 必填
platformInputMapping 的值必须是顶层字段名
customRequestBody 必须是 JSON 对象
customRequestBody 顶层字段不得与输入映射字段名冲突
submit_poll 模式必须填写 resultPathTemplate
submit_poll 模式必须能配置 externalRunId 和 status 输出映射
successStatuses 必须是 terminalStatuses 的子集
```

### 成功响应

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "agentId": "agt_001",
    "name": "Skyvern Agent",
    "invokeMode": "submit_poll",
    "status": "draft",
    "verifiedAt": null,
    "lastVerificationPassed": null,
    "createdAt": "2026-04-27T08:00:00Z",
    "updatedAt": "2026-04-27T08:00:00Z"
  }
}
```

### 失败响应：字段冲突

```json
{
  "code": 40002,
  "message": "customRequestBody 中的字段 prompt 与平台输入映射字段冲突。",
  "data": null
}
```

### 失败响应：轮询配置缺失

```json
{
  "code": 40002,
  "message": "submit_poll 模式下 resultPathTemplate 为必填字段。",
  "data": null
}
```

## 4. 获取 Agent 列表

```http
GET /api/v1/agents?includeArchived=false
```

### 查询参数

| 参数            | 默认值 | 作用                 |
| --------------- | ------ | -------------------- |
| includeArchived | false  | 是否返回已归档 Agent |
| status          | 无     | 按状态筛选           |

### 成功响应

```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "agentId": "agt_001",
      "name": "Skyvern Agent",
      "description": "通过 Skyvern API 执行 Web 自动化任务",
      "invokeMode": "submit_poll",
      "status": "active",
      "verifiedAt": "2026-04-27T08:10:00Z",
      "lastVerificationPassed": true,
      "canSubmitEvaluation": true,
      "canVerify": true,
      "canArchive": true,
      "canCopyCreate": true,
      "createdAt": "2026-04-27T08:00:00Z",
      "updatedAt": "2026-04-27T08:10:00Z"
    }
  ]
}
```

## 5. 获取 Agent 详情

```http
GET /api/v1/agents/{agentId}
```

### 作用

返回完整非敏感配置，用于详情页展示和复制新建预填。不会返回 secret 明文。

### 成功响应

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "agentId": "agt_001",
    "templateId": "http_submit_poll_basic",
    "name": "Skyvern Agent",
    "description": "通过 Skyvern API 执行 Web 自动化任务",
    "invokeMode": "submit_poll",
    "status": "active",
    "connection": {
      "baseUrl": "https://api.agent.example.com",
      "invokePath": "/v1/run/tasks",
      "resultPathTemplate": "/v1/run/tasks/{externalRunId}",
      "requestTimeoutSeconds": 30,
      "pollIntervalSeconds": 2,
      "pollTimeoutSeconds": 300
    },
    "auth": {
      "type": "api_key_header",
      "hasCredential": true,
      "publicConfig": {
        "headerName": "x-api-key",
        "hasSecret": true
      }
    },
    "platformInputMapping": {
      "task": "prompt",
      "entryUrl": "url",
      "timeoutSeconds": "timeout_sec",
      "sampleId": "case_id",
      "evaluationId": "job_id",
      "maxSteps": "max_steps"
    },
    "taskRenderMode": "goal_only",
    "customRequestBody": {
      "engine": "skyvern-2.0"
    },
    "requestOptions": {
      "structuredOutput": {
        "supported": true,
        "fieldAlias": "data_extraction_schema"
      }
    },
    "platformOutputMapping": {
      "externalRunId": "task_id",
      "status": "status",
      "finalAnswer": "result.answer",
      "errorMessage": "error.message"
    },
    "terminalStatuses": ["completed", "failed", "timed_out"],
    "successStatuses": ["completed"],
    "verifiedAt": "2026-04-27T08:10:00Z",
    "lastVerification": {
      "passed": true,
      "warnings": [],
      "errors": []
    },
    "actions": {
      "canSubmitEvaluation": true,
      "canVerify": true,
      "canArchive": true,
      "canCopyCreate": true
    },
    "createdAt": "2026-04-27T08:00:00Z",
    "updatedAt": "2026-04-27T08:10:00Z"
  }
}
```

### 失败响应

```json
{
  "code": 40400,
  "message": "Agent 不存在。",
  "data": null
}
```

## 6. 验证 Agent

```http
POST /api/v1/agents/{agentId}/verify
```

### 请求体

```json
{
  "timeoutSeconds": 90
}
```

### 验证通过响应

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "agentId": "agt_001",
    "passed": true,
    "status": "active",
    "verifiedAt": "2026-04-27T08:10:00Z",
    "warnings": [
      {
        "code": "POLL_TIMEOUT_LONG",
        "message": "轮询总超时时间较长，可能影响评测吞吐。"
      }
    ],
    "errors": []
  }
}
```

### 验证失败响应

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "agentId": "agt_001",
    "passed": false,
    "status": "invalid",
    "verifiedAt": "2026-04-27T08:10:00Z",
    "warnings": [],
    "errors": [
      {
        "code": "OUTPUT_MAPPING_NOT_FOUND",
        "message": "未能从响应路径 task_id 解析 externalRunId。"
      }
    ]
  }
}
```

### 状态冲突

```json
{
  "code": 40901,
  "message": "Agent 正在验证中，请稍后再试。",
  "data": null
}
```

## 7. 归档 Agent

```http
POST /api/v1/agents/{agentId}/archive
```

### 成功响应

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "agentId": "agt_001",
    "status": "archived",
    "updatedAt": "2026-04-27T08:20:00Z"
  }
}
```

### 失败响应

```json
{
  "code": 40901,
  "message": "已归档 Agent 不能重复归档。",
  "data": null
}
```

## 架构设计

## 2. 设计原则

### 2.1 单层 Agent 配置快照

Agent 表示一份可运行配置，不再拆成 Agent + Revision。一个 Agent 创建后保存完整运行配置，Evaluation 创建时冻结该配置。冻结后，即使 Agent 被归档、失效或复制新建，历史 Evaluation 仍可追溯。

Agent 保存内容：

| 类别       | 内容                                              | 作用                             |
| ---------- | ------------------------------------------------- | -------------------------------- |
| 基本信息   | name、description、invokeMode                     | 用于识别和展示                   |
| 连接配置   | baseUrl、invokePath、resultPathTemplate、超时参数 | 用于后端调用外部 Agent           |
| 鉴权配置   | none、bearer、api_key_header、custom_header       | 用于访问外部 Agent               |
| 输入映射   | platformInputMapping                              | 平台字段写入外部请求字段名       |
| 自定义字段 | customRequestBody                                 | 每次请求固定携带的字段和值       |
| 输出映射   | platformOutputMapping                             | 从外部响应中读取状态、结果和错误 |
| 状态集合   | terminalStatuses、successStatuses                 | 判断外部任务生命周期             |

### 2.2 核心配置不允许原地修改

Agent 创建后不允许直接修改核心运行配置：

```text
invokeMode
connection
auth
platformInputMapping
taskRenderMode
customRequestBody
requestOptions
platformOutputMapping
terminalStatuses
successStatuses
```

配置需要变化时使用“复制新建”。复制新建不新增 clone 接口，由前端读取 Agent 详情后预填注册页，再调用 `POST /api/v1/agents` 创建新 Agent。原 Agent 的 secret 不复制，新 Agent 必须重新填写凭据并重新验证。

### 2.3 Agent 模板由后端提供

注册模板影响请求结构、输出解析和默认终态集合，属于平台协议能力，不是单纯 UI 预设。首期模板存放在后端 `templates.py`，通过接口提供给前端，不建 `agent_templates` 表。

模板元信息采用：

```json
{
  "templateId": "http_submit_poll_basic",
  "name": "提交 + 轮询 Agent",
  "description": "适用于先提交任务，再通过运行 ID 轮询结果的 Agent。",
  "recommended": true,
  "sortOrder": 10,
  "level": "basic",
  "tags": ["推荐", "异步", "轮询"],
  "defaultConfig": {}
}
```

字段含义：

| 字段          | 作用                                |
| ------------- | ----------------------------------- |
| templateId    | 模板唯一标识，可记录到 Agent 来源中 |
| name          | 前端模板卡片标题                    |
| description   | 说明模板适用场景                    |
| recommended   | 控制推荐标签和默认选中              |
| sortOrder     | 控制展示顺序                        |
| level         | 标识 basic / advanced               |
| tags          | 展示“推荐、异步、轮询”等标签        |
| defaultConfig | 用于预填注册表单                    |

模板只用于初始化表单，Agent 运行时不依赖模板。

## 3. 字段名映射与字段值填写

注册页必须明确区分三类输入。

### 3.1 平台输入字段映射

用户填写外部 Agent 请求体字段名，不填写字段值。

示例：

```json
{
  "platformInputMapping": {
    "task": "prompt",
    "entryUrl": "url",
    "timeoutSeconds": "timeout_sec",
    "sampleId": "case_id",
    "evaluationId": "job_id",
    "maxSteps": "max_steps"
  }
}
```

含义：

```text
平台运行时把 task 的值写入 prompt
平台运行时把 entryUrl 的值写入 url
平台运行时把 timeoutSeconds 的值写入 timeout_sec
```

### 3.2 用户自定义固定字段

用户填写字段名和值。该对象会原样合并到每次请求体。

```json
{
  "customRequestBody": {
    "engine": "skyvern-2.0",
    "proxy_location": "RESIDENTIAL",
    "run_with": "agent"
  }
}
```

这些字段不是平台运行时动态生成的字段，而是用户希望每次请求都携带的固定参数。

### 3.3 输出字段映射

用户填写外部 Agent 响应 JSON 路径，不填写具体返回值。

```json
{
  "platformOutputMapping": {
    "externalRunId": "data.runId",
    "status": "data.status",
    "finalAnswer": "data.answer",
    "errorMessage": "data.error.message"
  }
}
```

含义是后端从响应对象中读取对应字段。
