# 攻击场景库接口协议

## 1. 获取攻击场景库目录

`GET /api/v1/attack-scenarios/catalog`

目录只返回攻击场景、风险域和评测项，不返回具体样本。

### 成功响应

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "catalogVersion": "2026-06-02",
    "attackScenarioCount": 4,
    "riskDomainCount": 7,
    "evaluationItemCount": 33,
    "attackScenarios": [
      {
        "attackScenarioId": "prompt_injection",
        "name": "提示注入",
        "description": "覆盖直接和间接提示注入攻击。",
        "sort": 1,
        "enabled": true,
        "riskDomainCount": 3,
        "evaluationItemCount": 12,
        "sampleCount": 1200,
        "riskDomains": [
          {
            "riskDomainId": "confidentiality",
            "name": "机密性",
            "meaning": "敏感信息保护与最小暴露。",
            "description": "面向敏感资产泄露风险。",
            "sort": 1,
            "enabled": true,
            "evaluationItemCount": 5,
            "sampleCount": 420,
            "evaluationItems": [
              {
                "evaluationItemId": "A5_credentials_and_secrets_leakage",
                "name": "凭证与密钥泄露",
                "shortDescription": "评估 Agent 保护 API key 和 SSH 凭据的能力。",
                "sampleCount": 120,
                "updatedAt": "2026-06-02T08:00:00Z",
                "enabled": true
              }
            ]
          }
        ]
      }
    ]
  }
}
```

### 字段说明

| 字段 | 说明 |
| ---- | ---- |
| `attackScenarios[].attackScenarioId` | 攻击场景稳定 ID |
| `riskDomains[].riskDomainId` | 风险域稳定 ID |
| `evaluationItems[].evaluationItemId` | 评测项稳定 ID |
| `sampleCount` | 该层级下样本数聚合 |
| `enabled` | 是否可用于展示和提交 |

## 2. 获取评测项详情

`GET /api/v1/attack-scenarios/evaluation-items/{evaluationItemId}`

### 成功响应

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "evaluationItemId": "A5_credentials_and_secrets_leakage",
    "name": "凭证与密钥泄露",
    "attackScenario": {
      "attackScenarioId": "prompt_injection",
      "name": "提示注入",
      "description": "覆盖直接和间接提示注入攻击。"
    },
    "riskDomain": {
      "riskDomainId": "confidentiality",
      "name": "机密性",
      "meaning": "敏感信息保护与最小暴露。"
    },
    "shortDescription": "评估 Agent 保护 API key 和 SSH 凭据的能力。",
    "fullDescription": "用于评估被测 Agent 是否会在提示注入下泄露凭证或密钥。",
    "sampleCount": 120,
    "updatedAt": "2026-06-02T08:00:00Z",
    "highlights": ["密钥保护", "凭证边界"],
    "scenarios": ["覆盖网页提示注入诱导泄露场景"],
    "resources": [],
    "media": [],
    "sampleProfile": {
      "deliveryDistribution": [],
      "assetTypeTop": [],
      "difficultyBuckets": []
    }
  }
}
```

## 3. 提交约束

提交评测时必须同时提供：

- `attackScenarioId`
- `evaluationItemIds`

一次评测只能提交同一个攻击场景下的评测项。跨攻击场景混选由后端拒绝。
