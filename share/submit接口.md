# submit接口

## 8. 获取评测提交元数据

```http
GET /api/v1/evaluations/meta
```

### 成功响应

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "submitMethods": ["api", "docker"],
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
      "default": 15
    },
    "maxSteps": {
      "min": 1,
      "max": 100,
      "default": 30
    },
    "leaderboardDisplayMode": {
      "default": "public",
      "options": ["public", "anonymous"]
    }
  }
}
```

## 9. 校验评测请求

```http
POST /api/v1/evaluations/validate
```

### API 方式请求

```json
{
  "submitMethod": "api",
  "agentId": "agt_001",
  "datasetIds": ["A1_identity_leakage"],
  "parameters": {
    "difficulty": 0.5,
    "timeoutMinutes": 20,
    "maxSteps": 30
  },
  "leaderboardDisplayMode": "public"
}
```

### 排行榜展示模式

新提交不再使用 `publicToLeaderboard=false` 表示不进榜。创建评测时必须使用 `leaderboardDisplayMode` 表达榜单展示方式：

| 值        | 含义                               |
| --------- | ---------------------------------- |
| public    | 成绩进入排行榜，展示智能体公开名称 |
| anonymous | 成绩进入排行榜，只展示匿名身份     |

### Docker 方式请求

```json
{
  "submitMethod": "docker",
  "docker": {
    "imageUri": "registry.example.com/web-agent:latest",
    "command": "python run.py",
    "env": {
      "AGENT_MODE": "eval"
    }
  },
  "datasetIds": ["A1_identity_leakage"],
  "parameters": {
    "difficulty": 0.5,
    "timeoutMinutes": 20,
    "maxSteps": 30
  },
  "leaderboardDisplayMode": "anonymous"
}
```

### 成功响应

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "ok": true,
    "warnings": [
      {
        "code": "VERIFICATION_OLDER_THAN_7_DAYS",
        "message": "该 Agent 最近一次验证已超过 7 天，建议重新验证。"
      }
    ]
  }
}
```

### 失败响应

```json
{
  "code": 40901,
  "message": "Agent 当前状态为 invalid，不能提交评测。",
  "data": {
    "agentId": "agt_001",
    "status": "invalid"
  }
}
```

## 10. 创建评测任务

```http
POST /api/v1/evaluations
```

### API 方式请求

```json
{
  "requestId": "submit_20260427_demo001",
  "submitMethod": "api",
  "agentId": "agt_001",
  "datasetIds": ["A1_identity_leakage"],
  "parameters": {
    "difficulty": 0.5,
    "timeoutMinutes": 20,
    "maxSteps": 30
  },
  "leaderboardDisplayMode": "public"
}
```

### Docker 方式请求

```json
{
  "requestId": "submit_20260427_demo002",
  "submitMethod": "docker",
  "docker": {
    "imageUri": "registry.example.com/web-agent:latest",
    "command": "python run.py",
    "env": {
      "AGENT_MODE": "eval"
    }
  },
  "datasetIds": ["A1_identity_leakage"],
  "parameters": {
    "difficulty": 0.5,
    "timeoutMinutes": 20,
    "maxSteps": 30
  },
  "leaderboardDisplayMode": "anonymous"
}
```

### 成功响应

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "evaluationId": "eval_20260427_080800_ab12cd",
    "submitMethod": "api",
    "agentId": "agt_001",
    "status": "queued",
    "createdAt": "2026-04-27T08:08:00Z"
  }
}
```

### 失败响应：已归档 Agent

```json
{
  "code": 40901,
  "message": "已归档 Agent 不能提交评测。",
  "data": {
    "agentId": "agt_001",
    "status": "archived"
  }
}
```

### 失败响应：requestId 冲突

```json
{
  "code": 40900,
  "message": "requestId 已被不同请求体使用。",
  "data": null
}
```

## 架构设计

## 4. 注册提交阶段资源

### 4.1 Agent

状态：

```text
draft
verifying
active
invalid
archived
```

状态操作规则：

| 状态      | 复制新建 |   验证 |   归档 | 提交评测 |
| --------- | -------: | -----: | -----: | -------: |
| draft     |     可以 |   可以 |   可以 |   不可以 |
| verifying |     可以 | 不可以 | 不建议 |   不可以 |
| active    |     可以 |   可以 |   可以 |     可以 |
| invalid   |     可以 |   可以 |   可以 |   不可以 |
| archived  |     可以 | 不可以 | 不可以 |   不可以 |

已归档或已失效 Agent 可以复制新建，因为旧配置仍有复用价值。

### 4.2 Evaluation

提交测评页创建 Evaluation。提交方式分为：

```text
api
docker
```

API 方式选择已注册且未归档 Agent。下拉框可展示未归档 Agent，但只有 `active` 状态允许提交。Docker 方式保持当前设计不变。

Evaluation 创建时冻结配置：

| submitMethod | 冻结内容             |
| ------------ | -------------------- |
| api          | frozenAgentSnapshot  |
| docker       | frozenDockerSnapshot |

Evaluation 对外主状态：

```text
queued
running
completed
failed
canceled
```

## 5. 页面架构

### 5.1 Agent 管理页

承担：

```text
查看 Agent 列表
查看状态
验证 Agent
归档 Agent
复制新建
提交评测
进入 Agent 详情页
```

### 5.2 Agent 注册页

采用左右布局：

```text
左侧：引导式配置工作区
右侧：curl / Python 实时代码预览
```

注册页步骤：

```text
选择模板
填写基本信息
配置连接与鉴权
配置输入字段映射
配置自定义固定字段
配置输出字段映射
确认并创建
```

### 5.3 Agent 详情页

必须保留。职责：

```text
查看完整非敏感配置
查看最近一次验证结果
验证
归档
复制新建
提交评测
```

### 5.4 提交测评页

保持当前页面设计。只调整提交智能体方式：

```text
API：选择已注册且未归档 Agent
Docker：保持原设计不变
```

## 6. 后端安全约束

### 6.1 SSRF 防护

注册 Agent 时用户提供 `baseUrl`，后端会主动请求该地址，必须限制：

```text
只允许 http / https
禁止 localhost、127.0.0.1、0.0.0.0
默认禁止内网 IP 段
限制重定向次数
重定向后重新校验地址
限制请求超时和响应体大小
```

### 6.2 凭据安全

Agent 详情不返回 secret 明文。复制新建只复制非敏感配置。用户必须重新填写 token、api key 或 header secret。

### 6.3 字段冲突校验

`customRequestBody` 的顶层字段不能与 `platformInputMapping` 映射出的外部字段名冲突。

冲突示例：

```json
{
  "platformInputMapping": {
    "task": "prompt"
  },
  "customRequestBody": {
    "prompt": "固定提示词"
  }
}
```

该配置会导致平台动态 task 值与固定字段冲突，后端必须拒绝。
