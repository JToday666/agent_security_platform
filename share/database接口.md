# 数据集与数据库辅助接口协议

## 1. 获取数据集列表

`GET /api/v1/datasets`

- **作用**：获取系统内已注册并启用的安全测试数据集清单。
- **响应**：

```json
{
  "code": 0,
  "data": {
    "items": [
      {
        "datasetId": "A1_identity_leakage",
        "name": "身份信息泄露",
        "sampleCount": 200,
        "difficultyAvg": 0.45
      }
    ]
  },
  "message": "success"
}
```

## 2. 获取数据集详情

`GET /api/v1/datasets/{datasetId}`

- **作用**：读取该数据集的指导规范、详细指标与包含的风险类型。
- **响应**：

```json
{
  "code": 0,
  "data": {
    "datasetId": "A1_identity_leakage",
    "description": "测试模型是否会越权搜集身份信息...",
    "tags": ["隐私", "越权"]
  },
  "message": "success"
}
```
