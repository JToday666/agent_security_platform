# API 接口协议

> 本文档基于 `2026-04-09` 对本地后端实现、数据库冒烟测试和真实 HTTP 冒烟脚本的验证结果整理。  
> 前端统一以本文为主协议；`user接口.md`、`database&submit接口.md`、`evaluations接口.md` 仅保留领域补充说明。

## 1. 通用约定

### 1.1 Base URL

```text
/api/v1
```

服务元信息接口额外包含：

- `GET /`
- `GET /api/`
- `GET /api/v1/`

### 1.2 统一响应包裹

成功：

```json
{
  "code": 0,
  "data": {},
  "message": "success"
}
```

失败：

```json
{
  "code": 1000,
  "data": null,
  "message": "错误描述"
}
```

前端依赖规则：

- `code === 0` 表示业务成功
- `code !== 0` 表示业务失败
- 所有公开接口都应返回 `{ code, data, message }`
- 请求参数校验失败也会返回 envelope，不应按 FastAPI 默认裸 `422` 结构处理

### 1.3 鉴权

- 需要登录的接口统一使用 `Authorization: Bearer <token>`
- 未登录、token 无效、token 已过期、token 对应用户不存在时，统一返回：

```json
{
  "code": 40100,
  "data": null,
  "message": "未登录或登录已失效。"
}
```

### 1.4 当前稳定错误码

| code    | HTTP  | 含义                     |
| ------- | ----- | ------------------------ |
| `0`     | `200` | 成功                     |
| `1000`  | `422` | 请求参数校验失败         |
| `1001`  | `401` | 用户名或密码错误         |
| `1002`  | `409` | 用户名或邮箱已被注册     |
| `1003`  | `409` | 用户名已被占用           |
| `1004`  | `403` | 邮箱不可修改             |
| `40002` | `400` | 提交参数不合法           |
| `40100` | `401` | 未登录或登录已失效       |
| `40300` | `403` | 无权访问目标资源         |
| `40400` | `404` | 目标不存在               |
| `40901` | `409` | 当前状态不允许执行该动作 |
| `40902` | `409` | 已达到暂停次数上限       |
| `500`   | `500` | 通用服务错误             |
| `50000` | `500` | 服务内部错误，请稍后重试 |

## 2. 服务元信息接口

### 2.1 `GET /`

- 路由：`GET /`
- 鉴权：否
- 请求类型：无

请求示例：

```http
GET / HTTP/1.1
Host: 127.0.0.1:8000
```

成功响应示例：

```json
{
  "code": 0,
  "data": {
    "message": "Hello FastAPI project! PROJECT_NAME: Agent Security Platform"
  },
  "message": "success"
}
```

### 2.2 `GET /api/`

- 路由：`GET /api/`
- 鉴权：否
- 请求类型：无

请求示例：

```http
GET /api/ HTTP/1.1
Host: 127.0.0.1:8000
```

成功响应示例：

```json
{
  "code": 0,
  "data": {
    "message": "Welcome to the API!"
  },
  "message": "success"
}
```

失败响应示例：

```json
{
  "code": 50000,
  "data": {
    "errorType": "RuntimeError"
  },
  "message": "服务内部错误，请稍后重试。"
}
```

### 2.3 `GET /api/v1/`

- 路由：`GET /api/v1/`
- 鉴权：否
- 请求类型：无

请求示例：

```http
GET /api/v1/ HTTP/1.1
Host: 127.0.0.1:8000
```

成功响应示例：

```json
{
  "code": 0,
  "data": {
    "message": "API v1!"
  },
  "message": "success"
}
```

失败响应示例：

```json
{
  "code": 50000,
  "data": {
    "errorType": "RuntimeError"
  },
  "message": "服务内部错误，请稍后重试。"
}
```

## 3. 认证与用户接口

### 3.1 用户登录

- 路由：`POST /api/v1/auth/login`
- 鉴权：否
- 请求类型：`application/json`

请求体示例：

```json
{
  "username": "alice",
  "password": "secret123"
}
```

成功响应示例：

```json
{
  "code": 0,
  "data": {
    "token": "<jwt-token>",
    "user": {
      "id": 1,
      "username": "alice",
      "email": "alice@example.com",
      "avatarUrl": null
    }
  },
  "message": "success"
}
```

失败响应示例：

```json
{
  "code": 1001,
  "data": null,
  "message": "用户名或密码错误"
}
```

### 3.2 用户注册

- 路由：`POST /api/v1/auth/register`
- 鉴权：否
- 请求类型：`application/json`

请求体示例：

```json
{
  "username": "alice",
  "email": "alice@example.com",
  "password": "secret123"
}
```

成功响应示例：

```json
{
  "code": 0,
  "data": {
    "token": "<jwt-token>",
    "user": {
      "id": 1,
      "username": "alice",
      "email": "alice@example.com",
      "avatarUrl": null
    }
  },
  "message": "success"
}
```

失败响应示例：

```json
{
  "code": 1002,
  "data": null,
  "message": "邮箱已被注册"
}
```

### 3.3 获取当前登录用户

- 路由：`GET /api/v1/auth/me`
- 鉴权：是
- 请求类型：无

请求示例：

```http
GET /api/v1/auth/me HTTP/1.1
Host: 127.0.0.1:8000
Authorization: Bearer <token>
```

成功响应示例：

```json
{
  "code": 0,
  "data": {
    "id": 1,
    "username": "alice",
    "email": "alice@example.com",
    "avatarUrl": "/uploads/avatars/1_demo.png"
  },
  "message": "success"
}
```

失败响应示例：

```json
{
  "code": 40100,
  "data": null,
  "message": "未登录或登录已失效。"
}
```

### 3.4 获取用户资料

- 路由：`GET /api/v1/user/profile`
- 鉴权：是
- 请求类型：无

请求示例：

```http
GET /api/v1/user/profile HTTP/1.1
Host: 127.0.0.1:8000
Authorization: Bearer <token>
```

成功响应示例：

```json
{
  "code": 0,
  "data": {
    "id": 1,
    "username": "alice",
    "email": "alice@example.com",
    "avatarUrl": "/uploads/avatars/1_demo.png"
  },
  "message": "success"
}
```

失败响应示例：

```json
{
  "code": 40100,
  "data": null,
  "message": "未登录或登录已失效。"
}
```

### 3.5 修改用户资料

- 路由：`PUT /api/v1/user/profile`
- 鉴权：是
- 请求类型：`application/json`
- 说明：当前允许修改 `username`、`password`；`email` 字段即使出现在请求体中，也会被业务拒绝

请求体示例：

```json
{
  "username": "alice_new",
  "password": "secret456"
}
```

成功响应示例：

```json
{
  "code": 0,
  "data": {
    "id": 1,
    "username": "alice_new",
    "email": "alice@example.com",
    "avatarUrl": "/uploads/avatars/1_demo.png"
  },
  "message": "success"
}
```

失败响应示例：

```json
{
  "code": 1004,
  "data": null,
  "message": "邮箱不可修改"
}
```

### 3.6 上传头像

- 路由：`POST /api/v1/user/avatar`
- 鉴权：是
- 请求类型：`multipart/form-data`
- 表单字段：`avatar`
- 限制：仅支持 `image/jpeg`、`image/png`，文件大小不超过 `2MB`

请求示例：

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/user/avatar" \
  -H "Authorization: Bearer <token>" \
  -F "avatar=@./avatar.png"
```

成功响应示例：

```json
{
  "code": 0,
  "data": {
    "avatarUrl": "/uploads/avatars/1_2f6ab0d8f3d44b9d9c0b55f2a62d23d0.png"
  },
  "message": "success"
}
```

失败响应示例：

```json
{
  "code": 1000,
  "data": null,
  "message": "请选择要上传的头像"
}
```

## 4. 数据集接口

### 4.1 获取数据集目录

- 路由：`GET /api/v1/datasets/catalog`
- 鉴权：否
- 请求类型：无

请求示例：

```http
GET /api/v1/datasets/catalog HTTP/1.1
Host: 127.0.0.1:8000
```

成功响应示例：

```json
{
  "code": 0,
  "data": {
    "catalogVersion": "2026-04-09T06:00:00Z",
    "categoryCount": 1,
    "subcategoryCount": 1,
    "categories": [
      {
        "categoryId": "confidentiality",
        "name": "机密性",
        "meaning": "敏感信息保护与最小暴露",
        "description": "面向敏感信息保护的风险大类。",
        "sort": 1,
        "enabled": true,
        "subcategoryCount": 1,
        "subcategories": [
          {
            "datasetId": "A1_identity_leakage",
            "name": "身份信息泄露",
            "shortDescription": "评估模型对身份字段的保护能力。",
            "sampleCount": 960,
            "updatedAt": "2026-04-09T06:00:00Z",
            "enabled": true
          }
        ]
      }
    ]
  },
  "message": "success"
}
```

失败响应示例：

```json
{
  "code": 50000,
  "data": {
    "errorType": "RuntimeError"
  },
  "message": "服务内部错误，请稍后重试。"
}
```

### 4.2 获取单个数据集详情

- 路由：`GET /api/v1/datasets/{datasetId}`
- 鉴权：否
- 请求类型：无
- Path 参数：`datasetId`

请求示例：

```http
GET /api/v1/datasets/A1_identity_leakage HTTP/1.1
Host: 127.0.0.1:8000
```

成功响应示例：

```json
{
  "code": 0,
  "data": {
    "datasetId": "A1_identity_leakage",
    "name": "身份信息泄露",
    "category": {
      "categoryId": "confidentiality",
      "name": "机密性",
      "meaning": "敏感信息保护与最小暴露"
    },
    "shortDescription": "评估模型对身份字段的保护能力。",
    "fullDescription": "该数据集覆盖身份信息查询、回显与越权诱导等场景。",
    "sampleCount": 960,
    "updatedAt": "2026-04-09T06:00:00Z",
    "highlights": ["覆盖多轮诱导泄露路径"],
    "scenarios": ["攻击者诱导披露个人身份信息"],
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
        "title": "样例概览",
        "description": "展示输入结构和安全边界。",
        "url": "https://example.com/media/A1.png",
        "coverUrl": null,
        "sort": 1
      }
    ]
  },
  "message": "success"
}
```

失败响应示例：

```json
{
  "code": 40400,
  "data": null,
  "message": "评测项不存在。"
}
```

## 5. 提交接口

### 5.1 获取提交页元数据

- 路由：`GET /api/v1/agents/submit-meta`
- 鉴权：否
- 请求类型：无

请求示例：

```http
GET /api/v1/agents/submit-meta HTTP/1.1
Host: 127.0.0.1:8000
```

成功响应示例：

```json
{
  "code": 0,
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
  },
  "message": "success"
}
```

失败响应示例：

```json
{
  "code": 50000,
  "data": {
    "errorType": "RuntimeError"
  },
  "message": "服务内部错误，请稍后重试。"
}
```

### 5.2 提交前预检查

- 路由：`POST /api/v1/agents/precheck`
- 鉴权：是
- 请求类型：`application/json`

请求体示例：

```json
{
  "agentName": "安全卫士 v1.0",
  "description": "夜间回归任务",
  "submitMethod": "api",
  "api": {
    "baseUrl": "https://example.com/agent",
    "token": "sk-demo"
  },
  "docker": null,
  "parameters": {
    "difficulty": 0.5,
    "timeoutMinutes": 20,
    "retryEnabled": false
  },
  "publicToLeaderboard": false,
  "datasetIds": ["A1_identity_leakage"],
  "requestId": "submit_20260409_demo001"
}
```

成功响应示例：

```json
{
  "code": 0,
  "data": {
    "ok": true,
    "warnings": []
  },
  "message": "success"
}
```

失败响应示例：

```json
{
  "code": 40002,
  "data": null,
  "message": "请至少选择一个评测项"
}
```

约束：

- `submitMethod` 只允许 `api` 或 `docker`
- `requestId` 长度 `6-128`，首字符必须是字母或数字，后续仅允许字母、数字、`_`、`-`
- `datasetIds` 不能为空，且不允许重复
- 当 `submitMethod = "api"` 时必须提供 `api`，不得同时提供 `docker`
- 当 `submitMethod = "docker"` 时必须提供 `docker`，不得同时提供 `api`

### 5.3 正式提交评测任务

- 路由：`POST /api/v1/agents/submit`
- 鉴权：是
- 请求类型：`application/json`
- 请求体：与 `POST /api/v1/agents/precheck` 相同
- 幂等：相同用户 + 相同 `requestId` 重复提交时，直接返回已存在任务

成功响应示例：

```json
{
  "code": 0,
  "data": {
    "evaluationId": "eval_20260409_062754_290fd4",
    "status": "pending",
    "createdAt": "2026-04-09T06:27:54Z"
  },
  "message": "success"
}
```

失败响应示例：

```json
{
  "code": 40100,
  "data": null,
  "message": "未登录或登录已失效。"
}
```

## 6. 评测记录接口

### 6.1 获取评测记录列表

- 路由：`GET /api/v1/evaluations`
- 鉴权：是
- 请求类型：无

请求示例：

```http
GET /api/v1/evaluations HTTP/1.1
Host: 127.0.0.1:8000
Authorization: Bearer <token>
```

成功响应示例：

```json
{
  "code": 0,
  "data": [
    {
      "evaluationId": "eval_20260409_062754_290fd4",
      "agentName": "安全卫士 v1.0",
      "description": "夜间回归任务",
      "createdAt": "2026-04-09T06:27:54Z",
      "updatedAt": "2026-04-09T06:27:54Z",
      "status": "pending",
      "progressPercent": 0,
      "finalReportAvailable": false,
      "finalizationReason": null,
      "publicToLeaderboard": false,
      "datasetIds": ["A1_identity_leakage"],
      "datasetNames": ["身份信息泄露"],
      "submitMethod": "api",
      "score": null,
      "ownerName": "alice",
      "parameters": {
        "difficulty": 0.5,
        "timeoutMinutes": 20,
        "retryEnabled": false
      }
    }
  ],
  "message": "success"
}
```

失败响应示例：

```json
{
  "code": 40100,
  "data": null,
  "message": "未登录或登录已失效。"
}
```

### 6.2 获取单个评测详情

- 路由：`GET /api/v1/evaluations/{evaluationId}`
- 鉴权：是
- 请求类型：无
- Path 参数：`evaluationId`

请求示例：

```http
GET /api/v1/evaluations/eval_20260409_062754_290fd4 HTTP/1.1
Host: 127.0.0.1:8000
Authorization: Bearer <token>
```

成功响应示例：

```json
{
  "code": 0,
  "data": {
    "evaluationId": "eval_20260409_062754_290fd4",
    "agentName": "安全卫士 v1.0",
    "description": "夜间回归任务",
    "createdAt": "2026-04-09T06:27:54Z",
    "updatedAt": "2026-04-09T06:27:54Z",
    "status": "pending",
    "score": null,
    "publicToLeaderboard": false,
    "datasetIds": ["A1_identity_leakage"],
    "datasetNames": ["身份信息泄露"],
    "submitMethod": "api",
    "ownerName": "alice",
    "parameters": {
      "difficulty": 0.5,
      "timeoutMinutes": 20,
      "retryEnabled": false
    },
    "progress": {
      "percent": 0,
      "totalDatasetCount": 1,
      "completedDatasetCount": 0,
      "runningDatasetId": null,
      "runningDatasetName": null,
      "pauseDeadlineAt": null,
      "statusText": "任务已创建，等待开始评测。"
    },
    "controls": {
      "canPause": false,
      "canResume": false,
      "canTerminate": false,
      "canCancel": true,
      "pauseUsed": false
    },
    "finalReportAvailable": false,
    "finalizationReason": null,
    "report": null
  },
  "message": "success"
}
```

失败响应示例：

```json
{
  "code": 40400,
  "data": null,
  "message": "评测记录不存在。"
}
```

### 6.3 对评测任务执行动作

- 路由：`POST /api/v1/evaluations/{evaluationId}/actions`
- 鉴权：是
- 请求类型：`application/json`
- 请求体字段：`action`
- 允许动作：`pause`、`resume`、`terminate`、`cancel`

请求体示例：

```json
{
  "action": "cancel"
}
```

成功响应示例：

```json
{
  "code": 0,
  "data": {
    "evaluationId": "eval_20260409_062754_290fd4",
    "agentName": "安全卫士 v1.0",
    "description": "夜间回归任务",
    "createdAt": "2026-04-09T06:27:54Z",
    "updatedAt": "2026-04-09T06:28:10Z",
    "status": "canceled",
    "score": null,
    "publicToLeaderboard": false,
    "datasetIds": ["A1_identity_leakage"],
    "datasetNames": ["身份信息泄露"],
    "submitMethod": "api",
    "ownerName": "alice",
    "parameters": {
      "difficulty": 0.5,
      "timeoutMinutes": 20,
      "retryEnabled": false
    },
    "progress": {
      "percent": 100,
      "totalDatasetCount": 1,
      "completedDatasetCount": 1,
      "runningDatasetId": null,
      "runningDatasetName": null,
      "pauseDeadlineAt": null,
      "statusText": "评测已取消。"
    },
    "controls": {
      "canPause": false,
      "canResume": false,
      "canTerminate": false,
      "canCancel": false,
      "pauseUsed": false
    },
    "finalReportAvailable": false,
    "finalizationReason": "canceled_by_user",
    "report": null
  },
  "message": "success"
}
```

失败响应示例：

```json
{
  "code": 40901,
  "data": null,
  "message": "当前状态不允许执行 pause 操作。"
}
```

动作语义：

- `pause`：仅 `running` 状态可用；允许当前数据集跑完后进入 `paused`
- `resume`：仅 `paused` 状态可用
- `terminate`：`running` / `pausing` / `paused` 可用；终止后保留最终报告
- `cancel`：`pending` / `running` / `pausing` / `paused` / `terminating` / `canceling` 可用；取消后不生成最终报告

## 7. 补充文档

- 用户域补充说明：[`user接口.md`](./user接口.md)
- 数据集与提交通用说明：[`database&submit接口.md`](./database&submit接口.md)
- 评测列表与动作语义补充：[`evaluations接口.md`](./evaluations接口.md)
