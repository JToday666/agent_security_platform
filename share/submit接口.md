# 提交接口协议

## 1. 获取评测提交元数据

`GET /api/v1/evaluations/meta`

### 成功响应

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "submitMethods": ["api"],
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
      "step": 1,
      "default": 30
    },
    "publicToLeaderboard": {
      "default": true
    },
    "leaderboardDisplayMode": {
      "default": "public",
      "options": ["public", "anonymous"]
    }
  }
}
```

### 说明

- 当前提交方式仅支持 `api`
- `publicToLeaderboard` 仅作为兼容默认值保留，创建请求不接受 `false`
- 榜单展示方式以 `leaderboardDisplayMode` 为准，`anonymous` 表示仅匿名展示

## 2. 校验评测请求

`POST /api/v1/evaluations/validate`

### 请求体

```json
{
  "requestId": "submit_20260523_demo001",
  "submitMethod": "api",
  "agentId": "agt_001",
  "attackScenarioId": "prompt_injection",
  "evaluationItemIds": ["A1_identity_leakage"],
  "parameters": {
    "difficulty": 0.5,
    "timeoutMinutes": 20,
    "maxSteps": 30
  },
  "publicToLeaderboard": true,
  "leaderboardDisplayMode": "public"
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
  "message": "Agent 当前状态不允许提交评测。",
  "data": {
    "agentId": "agt_001",
    "status": "invalid"
  }
}
```

## 3. 创建评测任务

`POST /api/v1/evaluations`

### 请求体

```json
{
  "requestId": "submit_20260523_demo001",
  "submitMethod": "api",
  "agentId": "agt_001",
  "attackScenarioId": "prompt_injection",
  "evaluationItemIds": ["A1_identity_leakage"],
  "parameters": {
    "difficulty": 0.5,
    "timeoutMinutes": 20,
    "maxSteps": 30
  },
  "publicToLeaderboard": true,
  "leaderboardDisplayMode": "public"
}
```

### 成功响应

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "evaluationId": "eval_20260523_080800_ab12cd",
    "submitMethod": "api",
    "agentId": "agt_001",
    "status": "pending",
    "createdAt": "2026-05-23T08:08:00Z"
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

## 4. 当前约束

- `submitMethod` 目前只支持 `api`
- 必须提交 `attackScenarioId`，且 `evaluationItemIds` 必须全部属于该攻击场景
- `publicToLeaderboard=false` 已废弃，后端会直接拒绝
- `leaderboardDisplayMode` 取值为 `public` 或 `anonymous`
- `requestId` 用于幂等去重，相同请求体可复用同一任务，不同请求体会触发冲突
- Docker 提交方式当前未开放
