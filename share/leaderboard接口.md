# leaderboard接口

## 1. 获取当前排行榜

```http
GET /api/v1/leaderboards/current
```

### 作用

返回当前发布的排行榜快照。页面只展示一份当前榜单，前端可在本地按分数列排序。

### 成功响应

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "snapshotCode": "lb_20260505_140000",
    "entryCount": 2,
    "entries": [
      {
        "rankNo": 1,
        "displayName": "Aurora Guard",
        "anonymous": false,
        "officialConservativeScore": 93.6,
        "safeCapabilityScore": 91.4,
        "highDifficultyScore": 88.2,
        "unsafeRiskScore": 3.8,
        "confidence": 95.1,
        "verificationTier": "verified",
        "safetyCertification": "certified",
        "totalSamples": 260
      },
      {
        "rankNo": 2,
        "displayName": "Anonymous Agent",
        "anonymous": true,
        "officialConservativeScore": 90.8,
        "safeCapabilityScore": 89.7,
        "highDifficultyScore": 84.5,
        "unsafeRiskScore": 5.2,
        "confidence": 92.4,
        "verificationTier": "verified",
        "safetyCertification": "certified",
        "totalSamples": 240
      }
    ]
  }
}
```

### 字段说明

| 字段                      | 作用                                     |
| ------------------------- | ---------------------------------------- |
| snapshotCode              | 快照编号，供接口追踪使用，前端页面不展示 |
| entryCount                | 当前榜单条目数                           |
| entries[].rankNo          | 后端生成快照时的排名                     |
| entries[].displayName     | 页面展示名称；匿名条目固定返回匿名展示名 |
| entries[].anonymous       | 是否匿名展示                             |
| officialConservativeScore | 综合分                                   |
| safeCapabilityScore       | 安全能力分                               |
| highDifficultyScore       | 高难分                                   |
| unsafeRiskScore           | 风险分，数值越低代表风险越低             |
| confidence                | 置信度                                   |
| verificationTier          | 后端分层字段，当前前端页面不展示         |
| safetyCertification       | 后端认证字段，当前前端页面不展示         |
| totalSamples              | 参与评分的样本数                         |

### 失败响应

```json
{
  "code": 40400,
  "message": "当前排行榜不存在。",
  "data": null
}
```

## 2. 生成排行榜快照

```http
POST /api/v1/leaderboards/snapshots
```

### 请求体

```json
{
  "scoreModelVersion": "score_v1_5",
  "benchmarkVersion": "bm_v1"
}
```

### 作用

根据已发布评分结果生成新的排行榜快照。该接口需要登录，当前用于管理侧或运维侧生成快照，不直接由排行榜页面调用。

匿名规则：

- `leaderboardDisplayMode=public` 的评测结果以智能体公开名称进入榜单
- `leaderboardDisplayMode=anonymous` 的评测结果进入榜单，但只返回匿名展示名
- 历史 `publicToLeaderboard=false` 的评测结果不进入新快照

### 成功响应

响应结构与“获取当前排行榜”一致。
