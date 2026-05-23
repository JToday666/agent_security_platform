# report接口

## 1. 获取评测记录列表

`GET /api/v1/evaluations`

### 作用

返回当前用户的评测记录列表。列表接口只负责列表，不返回趋势图、独立报告页或样本下载入口。

### 成功响应

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "evaluationId": "eval_001",
        "agentName": "Skyvern Agent",
        "description": "通过 Skyvern API 执行 Web 自动化任务",
        "createdAt": "2026-05-23T08:00:00Z",
        "updatedAt": "2026-05-23T08:30:00Z",
        "status": "completed",
        "progressPercent": 100,
        "finalReportAvailable": true,
        "finalizationReason": null,
        "publicToLeaderboard": true,
        "leaderboardDisplayMode": "anonymous",
        "datasetIds": ["A1_identity_leakage"],
        "datasetNames": ["身份信息泄露"],
        "submitMethod": "api",
        "score": 72.4,
        "ownerName": "user1",
        "parameters": {
          "difficulty": 0.5,
          "timeoutMinutes": 20,
          "retryEnabled": false,
          "maxSteps": 30
        }
      }
    ]
  }
}
```

### 列表项说明

| 字段                     | 说明                       |
| ------------------------ | -------------------------- |
| `progressPercent`        | 任务进度百分比             |
| `finalReportAvailable`   | 任务级摘要是否已可用       |
| `finalizationReason`     | 终态说明                   |
| `publicToLeaderboard`    | 历史兼容字段               |
| `leaderboardDisplayMode` | 当前榜单展示方式           |
| `score`                  | 当前已存评测分数，可能为空 |

## 2. 获取评测详情

`GET /api/v1/evaluations/{evaluationId}`

### 作用

返回基础信息、进度、任务动作控制和任务级报告摘要。该接口不提供独立的趋势图接口，也不返回前端自组装的 `sampleSummary`、`representativeSamples` 或 `downloads` 字段。

### 成功响应

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "evaluationId": "eval_20260523_ab12cd",
    "agentName": "Skyvern Agent",
    "description": "通过 Skyvern API 执行 Web 自动化任务",
    "createdAt": "2026-05-23T08:00:00Z",
    "updatedAt": "2026-05-23T08:30:00Z",
    "status": "completed",
    "score": 72.4,
    "publicToLeaderboard": true,
    "leaderboardDisplayMode": "public",
    "datasetIds": ["A1_identity_leakage"],
    "datasetNames": ["身份信息泄露"],
    "submitMethod": "api",
    "ownerName": "user1",
    "parameters": {
      "difficulty": 0.5,
      "timeoutMinutes": 20,
      "retryEnabled": false,
      "maxSteps": 30
    },
    "progress": {
      "percent": 100,
      "totalDatasetCount": 1,
      "completedDatasetCount": 1,
      "runningDatasetId": null,
      "runningDatasetName": null,
      "pauseDeadlineAt": null,
      "statusText": "评测已完成。"
    },
    "controls": {
      "canPause": false,
      "canResume": false,
      "canTerminate": false,
      "canCancel": false,
      "pauseUsed": false
    },
    "finalReportAvailable": true,
    "finalizationReason": null,
    "report": {
      "reportStatus": "available",
      "summary": {
        "totalSamples": 20,
        "completedSamples": 20,
        "taskCompletedCount": 12,
        "harmDetectedCount": 5,
        "failedCount": 3,
        "byRiskCategory": [],
        "byRiskLevel": [],
        "byAttackLevel": []
      },
      "reportUri": null
    }
  }
}
```

### 详情字段说明

| 字段                             | 说明                       |
| -------------------------------- | -------------------------- |
| `progress.totalDatasetCount`     | 数据集数                   |
| `progress.completedDatasetCount` | 已完成数据集数             |
| `progress.runningDatasetId`      | 当前运行的数据集 ID        |
| `progress.pauseDeadlineAt`       | 暂停截止时间               |
| `controls`                       | 当前可执行动作集合         |
| `finalReportAvailable`           | 任务级报告是否可用         |
| `report.reportStatus`            | 报告状态                   |
| `report.summary`                 | 任务级汇总摘要             |
| `report.reportUri`               | 报告文件地址，当前预留为空 |

## 3. 获取评测评分

`GET /api/v1/evaluations/{evaluationId}/score`

### 成功响应

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "evaluationId": "eval_20260523_ab12cd",
    "officialConservativeScore": 72.4,
    "safeCapabilityScore": 78.1,
    "completionScore": 69.4,
    "safetyScore": 81.2,
    "unsafeRiskScore": 18.8,
    "highDifficultyScore": 61.9,
    "operationalUtilityScore": 74.5,
    "confidence": 80.5,
    "confidenceInterval90": [70.1, 84.2],
    "verificationTier": "verified",
    "safetyCertification": "certified"
  }
}
```

### 失败响应

```json
{
  "code": 40400,
  "message": "评分结果不存在，请先触发重算。",
  "data": null
}
```

## 4. 重算评测评分

`POST /api/v1/evaluations/{evaluationId}/score/recalculate`

### 请求体

```json
{
  "scoreModelVersion": "score_v1_5",
  "benchmarkVersion": "bm_v1"
}
```

### 成功响应

响应结构与“获取评测评分”一致。

### 失败响应

```json
{
  "code": 40903,
  "message": "评测尚未结束，不能计算评分。",
  "data": null
}
```

## 5. 执行评测动作

`POST /api/v1/evaluations/{evaluationId}/actions`

### 请求体

```json
{
  "action": "pause"
}
```

### 允许值

- `pause`
- `resume`
- `terminate`
- `cancel`

### 成功响应

返回与评测详情相同的详情快照，前端据此刷新状态和控制按钮。

### 失败响应

```json
{
  "code": 40901,
  "message": "当前状态不允许执行 pause 操作。",
  "data": null
}
```

## 6. 当前未实现能力

- 独立 `GET /api/v1/evaluations/score-trend` 趋势接口未实现
- 独立 `GET /api/v1/evaluations/{evaluationId}/report` 报告接口未实现
- 独立 `GET /api/v1/evaluations/{evaluationId}/samples/export` 样本明细导出接口未实现
- 独立回放或单样本证据查询接口未实现
- `report_uri` 当前预留为空，只保留任务级 `summary_json`
