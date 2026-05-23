# 数据集接口协议

## 1. 获取数据集目录

`GET /api/v1/datasets/catalog`

### 成功响应

```json
{
  "code": 0,
  "data": {
    "catalogVersion": "2026-05-23",
    "categoryCount": 2,
    "subcategoryCount": 6,
    "categories": [
      {
        "categoryId": "integrity",
        "name": "完整性",
        "meaning": "防止未授权修改与破坏。",
        "description": "面向篡改、注入、执行劫持和系统控制的风险大类。",
        "sort": 20,
        "enabled": true,
        "subcategoryCount": 3,
        "subcategories": [
          {
            "datasetId": "B2_Cloud_File_Modification",
            "name": "云文件修改",
            "shortDescription": "测试模型是否会执行文件修改类风险动作。",
            "sampleCount": 24,
            "updatedAt": "2026-05-20T08:00:00Z",
            "enabled": true
          }
        ]
      }
    ]
  },
  "message": "success"
}
```

### 目录项字段

| 字段                               | 说明                   |
| ---------------------------------- | ---------------------- |
| `catalogVersion`                   | 目录版本号             |
| `categoryCount`                    | 风险大类数量           |
| `subcategoryCount`                 | 数据集数量             |
| `categories[].categoryId`          | 风险大类稳定 ID        |
| `categories[].subcategoryCount`    | 当前大类下的数据集数量 |
| `subcategories[].datasetId`        | 数据集稳定 ID          |
| `subcategories[].shortDescription` | 数据集短描述           |
| `subcategories[].sampleCount`      | 样本数                 |
| `subcategories[].updatedAt`        | 最近更新时间           |

## 2. 获取数据集详情

`GET /api/v1/datasets/{datasetId}`

### 成功响应

```json
{
  "code": 0,
  "data": {
    "datasetId": "B2_Cloud_File_Modification",
    "name": "云文件修改",
    "category": {
      "categoryId": "integrity",
      "name": "完整性",
      "meaning": "防止未授权修改与破坏。"
    },
    "shortDescription": "测试模型是否会执行文件修改类风险动作。",
    "fullDescription": "用于评估被测 Agent 是否会在不应修改文件时执行破坏性文件操作。",
    "sampleCount": 24,
    "updatedAt": "2026-05-20T08:00:00Z",
    "highlights": ["文件写入", "目录遍历", "权限边界"],
    "scenarios": ["覆盖云端文件修改风险场景"],
    "resources": [
      {
        "label": "样本首页",
        "url": "/datasets/B2_Cloud_File_Modification/index.html"
      }
    ],
    "media": [
      {
        "title": "目录截图",
        "url": "/datasets/B2_Cloud_File_Modification/preview.png",
        "description": "展示样本入口页的页面截图"
      }
    ]
  },
  "message": "success"
}
```

### 详情字段说明

| 字段                  | 说明                                        |
| --------------------- | ------------------------------------------- |
| `datasetId`           | 数据集稳定 ID                               |
| `category.categoryId` | 风险大类稳定 ID                             |
| `category.meaning`    | 风险含义说明                                |
| `shortDescription`    | 数据集短描述                                |
| `fullDescription`     | 数据集长描述                                |
| `highlights`          | 重点摘要列表                                |
| `scenarios`           | 典型场景列表                                |
| `resources`           | 资源链接数组，元素至少包含 `label` 和 `url` |
| `media`               | 媒体资源数组，元素至少包含 `title` 和 `url` |
