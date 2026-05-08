# report接口

## 1. 获取评测记录列表

```http
GET /api/v1/evaluations?page=1&pageSize=20
```

### 作用

返回评测记录列表。列表接口只负责列表，不返回趋势图数据。

### 成功响应

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "evaluationId": "eval_001",
        "submitMethod": "api",
        "agentId": "agt_001",
        "agentName": "Skyvern Agent",
        "status": "completed",
        "score": 72.4,
        "createdAt": "2026-04-27T08:00:00Z",
        "updatedAt": "2026-04-27T08:30:00Z",
        "finishedAt": "2026-04-27T08:30:00Z",
        "publicToLeaderboard": true,
        "leaderboardDisplayMode": "anonymous",
        "datasetIds": ["A1_identity_leakage"],
        "datasetNames": ["身份信息泄露"],
        "parameters": {
          "difficulty": 0.5,
          "timeoutMinutes": 20,
          "maxSteps": 30
        },
        "sampleSummary": {
          "total": 20,
          "success": 12,
          "failed": 5,
          "error": 3
        },
        "finalReportAvailable": true
      }
    ],
    "page": 1,
    "pageSize": 20,
    "total": 1
  }
}
```

### 失败响应

```json
{
  "code": 40100,
  "message": "未登录或登录失效。",
  "data": null
}
```

### 榜单状态说明

评测记录和详情会同时返回历史兼容字段 `publicToLeaderboard` 与当前字段 `leaderboardDisplayMode`。前端展示时按以下规则派生榜单状态：

| 条件                                                             | 展示   |
| ---------------------------------------------------------------- | ------ |
| `publicToLeaderboard=false`                                      | 未排行 |
| `publicToLeaderboard=true` 且 `leaderboardDisplayMode=anonymous` | 匿名   |
| `publicToLeaderboard=true` 且 `leaderboardDisplayMode=public`    | 公开   |

## 2. 获取评测分数趋势

```http
GET /api/v1/evaluations/score-trend?scope=recent10
GET /api/v1/evaluations/score-trend?scope=all
```

### 查询参数

| 参数  | 默认值   | 作用            |
| ----- | -------- | --------------- |
| scope | recent10 | recent10 或 all |

### 成功响应

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "scope": "recent10",
    "defaultScope": "recent10",
    "defaultView": "capability",
    "views": {
      "capability": {
        "label": "能力视图",
        "metrics": ["conservativeScore", "performanceScore", "hardScore"]
      },
      "risk": {
        "label": "风险视图",
        "metrics": ["conservativeScore", "confidence", "unsafeRate"]
      }
    },
    "items": [
      {
        "evaluationId": "eval_001",
        "agentName": "Skyvern Agent",
        "createdAt": "2026-04-20T08:00:00Z",
        "finishedAt": "2026-04-20T08:30:00Z",
        "scores": {
          "conservativeScore": 61.2,
          "performanceScore": 69.4,
          "hardScore": 44.3,
          "confidence": 70.1,
          "unsafeRate": 14.2
        }
      },
      {
        "evaluationId": "eval_002",
        "agentName": "Skyvern Agent",
        "createdAt": "2026-04-27T08:00:00Z",
        "finishedAt": "2026-04-27T08:30:00Z",
        "scores": {
          "conservativeScore": 72.4,
          "performanceScore": 78.1,
          "hardScore": 61.9,
          "confidence": 80.5,
          "unsafeRate": 9.8
        }
      }
    ]
  }
}
```

### 字段说明

| 字段                     | 作用                       |
| ------------------------ | -------------------------- |
| defaultView              | 前端默认展示能力视图       |
| views.capability.metrics | 综合分、表现分、高难表现分 |
| views.risk.metrics       | 综合分、置信度、风险率     |
| items                    | 按时间升序排列的数据点     |
| scores                   | 每个点的折线指标           |

### 失败响应

```json
{
  "code": 40002,
  "message": "scope 只能是 recent10 或 all。",
  "data": null
}
```

## 3. 获取评测详情

```http
GET /api/v1/evaluations/{evaluationId}
```

### 作用

返回基础信息、状态、进度、代表样本和下载入口。不返回报告分析、不返回样本列表、不返回步骤记录。

### 成功响应

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "evaluationId": "eval_20260427_ab12cd",
    "submitMethod": "api",
    "agentId": "agt_001",
    "agentName": "Skyvern Agent",
    "status": "completed",
    "score": 72.4,
    "createdAt": "2026-04-27T08:00:00Z",
    "updatedAt": "2026-04-27T08:30:00Z",
    "startedAt": "2026-04-27T08:01:00Z",
    "finishedAt": "2026-04-27T08:30:00Z",
    "publicToLeaderboard": true,
    "leaderboardDisplayMode": "public",
    "datasetIds": ["A1_identity_leakage"],
    "datasetNames": ["身份信息泄露"],
    "parameters": {
      "difficulty": 0.5,
      "timeoutMinutes": 20,
      "maxSteps": 30
    },
    "progress": {
      "percent": 100,
      "totalSampleCount": 20,
      "completedSampleCount": 20,
      "statusText": "评测已完成。"
    },
    "sampleSummary": {
      "total": 20,
      "success": 12,
      "failed": 5,
      "error": 3
    },
    "representativeSamples": {
      "success": {
        "sampleId": "sample_001",
        "datasetName": "身份信息泄露",
        "normalizedResult": "success",
        "outcomeReasonText": "样本安全完成。",
        "replayUrl": "/api/v1/evaluations/eval_20260427_ab12cd/samples/sample_001/replay"
      },
      "failed": {
        "sampleId": "sample_009",
        "datasetName": "身份信息泄露",
        "normalizedResult": "failed",
        "outcomeReasonText": "Oracle 判定存在不安全行为。",
        "replayUrl": "/api/v1/evaluations/eval_20260427_ab12cd/samples/sample_009/replay"
      }
    },
    "downloads": {
      "sampleDetailsUrl": "/api/v1/evaluations/eval_20260427_ab12cd/samples/export"
    },
    "controls": {
      "canCancel": false
    },
    "finalReportAvailable": true
  }
}
```

### 只有一种结果时的响应片段

```json
{
  "representativeSamples": {
    "success": {
      "sampleId": "sample_001",
      "datasetName": "身份信息泄露",
      "normalizedResult": "success",
      "outcomeReasonText": "样本安全完成。",
      "replayUrl": "/api/v1/evaluations/eval_xxx/samples/sample_001/replay"
    },
    "failed": null
  }
}
```

### 失败响应

```json
{
  "code": 40400,
  "message": "Evaluation 不存在。",
  "data": null
}
```

## 4. 获取评测报告

```http
GET /api/v1/evaluations/{evaluationId}/report
```

### 作用

返回评分指标和绘图所需业务数据。不返回 `chartData`，不返回前端图表配置。

### 成功响应

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "evaluationId": "eval_20260427_ab12cd",
    "status": "ready",
    "generatedAt": "2026-04-27T08:30:00Z",
    "scores": {
      "conservativeScore": 72.4,
      "performanceScore": 78.1,
      "confidence": 80.5,
      "completionScore": 83.2,
      "safetyScore": 76.4,
      "hardScore": 61.9,
      "unsafeRate": 9.8,
      "timeScore": 66.3
    },
    "rawStats": {
      "total": 20,
      "success": 12,
      "failed": 5,
      "error": 3,
      "completionRate": 0.85,
      "successRate": 0.6,
      "conditionalSuccessRate": 0.7059
    },
    "posteriorInterval": {
      "psQ05": 72.4,
      "psQ50": 77.8,
      "psQ95": 84.1
    },
    "coverage": {
      "difficultyBucketHitCount": 5,
      "difficultyCoverageRatio": 1.0
    },
    "breakdowns": {
      "outcomeSummary": {
        "success": 12,
        "failed": 5,
        "error": 3
      },
      "difficultyBuckets": [
        {
          "bucket": "0.0-0.2",
          "total": 3,
          "success": 3,
          "failed": 0,
          "error": 0,
          "successRate": 1.0
        }
      ],
      "datasetSummaries": [
        {
          "datasetId": "A1_identity_leakage",
          "datasetName": "身份信息泄露",
          "total": 10,
          "success": 7,
          "failed": 2,
          "error": 1
        }
      ],
      "sampleScatterPoints": [
        {
          "sampleId": "sample_001",
          "difficulty": 0.62,
          "durationMs": 18234,
          "normalizedResult": "success"
        },
        {
          "sampleId": "sample_009",
          "difficulty": 0.81,
          "durationMs": 24120,
          "normalizedResult": "failed"
        }
      ]
    },
    "versions": {
      "difficultyVersion": "dv_2026q2_v1",
      "scoreModelVersion": "score_v1",
      "benchmarkVersion": "bm_v1"
    }
  }
}
```

### 失败响应：报告未生成

```json
{
  "code": 40902,
  "message": "评测报告尚未生成。",
  "data": {
    "evaluationId": "eval_20260427_ab12cd",
    "status": "running"
  }
}
```

## 5. 获取样本回放

```http
GET /api/v1/evaluations/{evaluationId}/samples/{sampleId}/replay
```

### 成功响应

返回视频流：

```text
Content-Type: video/mp4
```

### 失败响应

```json
{
  "code": 40400,
  "message": "样本回放不存在。",
  "data": null
}
```

## 6. 下载全部样本明细

```http
GET /api/v1/evaluations/{evaluationId}/samples/export
```

### 成功响应

```text
Content-Type: application/zip
Content-Disposition: attachment; filename="evaluation_eval_20260427_ab12cd_samples.zip"
```

ZIP 结构：

```text
manifest.json
samples.csv
samples/sample_001/summary.json
samples/sample_001/steps.jsonl
samples/sample_001/replay_manifest.json
```

manifest 示例：

```json
{
  "evaluationId": "eval_20260427_ab12cd",
  "generatedAt": "2026-04-27T08:35:00Z",
  "sampleCount": 20,
  "containsVideoFiles": false
}
```

### 失败响应

```json
{
  "code": 40400,
  "message": "样本明细文件不存在。",
  "data": null
}
```

## 7. 取消评测任务

```http
POST /api/v1/evaluations/{evaluationId}/cancel
```

### 成功响应

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "evaluationId": "eval_20260427_ab12cd",
    "status": "canceled",
    "updatedAt": "2026-04-27T08:12:00Z"
  }
}
```

### 失败响应

```json
{
  "code": 40902,
  "message": "当前评测状态为 completed，不能取消。",
  "data": {
    "evaluationId": "eval_20260427_ab12cd",
    "status": "completed"
  }
}
```

## 架构设计

## 2. 页面边界

### 2.1 评测记录页

保持当前设计不变，仅在英雄区和列表之间插入折线图。

折线图范围：

```text
最近 10 次
全部评测
```

默认范围：

```text
最近 10 次
```

折线图视图：

```text
能力视图：综合分、表现分、高难表现分
风险视图：综合分、置信度、风险率
```

默认视图：

```text
能力视图
```

趋势图不按 Agent 查询，只按当前用户最近或全部有报告的 Evaluation 查询。

### 2.2 评测详情页

详情页展示：

```text
基础信息
样本三态统计
报告指标表格
指标意义解释
核心能力雷达图
三态结果环形图
难度桶表现柱状图
数据集结果堆叠柱状图
样本难度 - 结果散点图
一个成功样本回放
一个失败或异常样本回放
全部样本明细下载按钮
```

不展示：

```text
样本列表
样本步骤记录
完整日志
完整 raw result
报告导出
```

## 3. 接口边界

详情页由两个主接口驱动：

```http
GET /api/v1/evaluations/{evaluationId}
GET /api/v1/evaluations/{evaluationId}/report
```

职责：

| 接口     | 负责                                     | 不负责                   |
| -------- | ---------------------------------------- | ------------------------ |
| 详情接口 | 基础信息、状态、进度、代表样本、下载入口 | 评分图表和指标解释数据   |
| 报告接口 | 评分指标、统计、breakdowns、版本信息     | 样本视频、步骤、下载文件 |

报告接口保留，但不做独立报告页。详情页分别请求两个接口，并在同一个页面内展示。

## 4. 报告数据结构

后端不返回 `chartData` 或前端图表配置。后端返回业务数据：

```text
scores
rawStats
posteriorInterval
coverage
breakdowns
versions
```

前端根据这些数据动态绘制五个图表。

理由：

```text
图表样式属于前端
业务统计属于后端
后端返回业务数据更容易复用
更换图表库不影响后端
```

## 5. 五个图表

### 5.1 核心能力雷达图

使用：

```text
performanceScore
completionScore
safetyScore
hardScore
timeScore
100 - unsafeRate
```

`unsafeRate` 是反向指标，雷达图中使用 `100 - unsafeRate` 表示安全稳定性。

### 5.2 三态结果环形图

使用：

```text
success
failed
error
```

用于区分安全成功、完成但不安全、运行异常三类结果。

### 5.3 难度桶表现柱状图

按难度桶展示：

```text
0.0-0.2
0.2-0.4
0.4-0.6
0.6-0.8
0.8-1.0
```

每个桶展示 success / failed / error 或 successRate。

### 5.4 数据集结果堆叠柱状图

每个数据集一根柱，内部堆叠：

```text
success
failed
error
```

用于查看不同风险类型表现差异。

### 5.5 样本难度 - 结果散点图

横轴：

```text
difficulty
```

纵轴：

```text
durationMs
```

点类型：

```text
success / failed / error
```

用于判断失败和异常是否集中在高难度或高耗时区域。

## 6. 代表样本回放

详情页只展示代表性样本的最小信息：

```json
{
  "sampleId": "sample_001",
  "datasetName": "身份信息泄露",
  "normalizedResult": "failed",
  "outcomeReasonText": "Oracle 判定存在不安全行为。",
  "replayUrl": "/api/v1/evaluations/eval_xxx/samples/sample_001/replay"
}
```

选择规则：

```text
优先展示 1 个 success + 1 个 failed
没有 failed 但有 error 时展示 success + error
只有 success 时只展示 1 个 success
只有 failed/error 时只展示 1 个 failed/error
没有可回放样本时展示暂无可回放样本
```

代表样本由后端在 Evaluation 完成时确定，保证详情页展示稳定。

## 7. 样本明细下载

详情页提供：

```http
GET /api/v1/evaluations/{evaluationId}/samples/export
```

下载包包含：

```text
manifest.json
samples.csv
summary.json
steps.jsonl
replay_manifest.json
```

首期默认不把所有视频打入 ZIP。视频体积大，直接打包会造成下载慢和失败率高。下载包中提供回放索引，后续可增加 `includeVideo=true` 支持完整离线证据包。

## 8. 数据流

### 8.1 评测记录页

```text
请求评测列表
请求 score-trend?scope=recent10
展示英雄区
展示趋势图
展示列表
切换全部评测时请求 score-trend?scope=all
切换能力/风险视图时不重新请求
```

### 8.2 评测详情页

```text
请求 Evaluation 详情
渲染基础信息和代表样本
如果 finalReportAvailable=true，请求 report
渲染指标表格、解释和图表
点击回放访问 replayUrl
点击下载访问 samples/export
```

## 9. 安全边界

所有接口必须校验：

```text
evaluation.owner_user_id == current_user.id
```

视频和下载包不返回永久公开地址。下载包和回放接口必须鉴权。

导出内容需要脱敏：

```text
不包含 Agent secret
不包含鉴权 header 明文
不包含服务器本地路径
不包含对象存储永久地址
不包含内部异常堆栈
```
