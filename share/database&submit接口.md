# database&submit接口

## 1. 文档目标

本文档面向后端开发，描述当前前端在"数据集"和"提交智能体"相关页面上已经固定下来的接口交互契约。

本次文档覆盖完整提交流程涉及的全部接口：

- `GET /api/v1/agents/submit-meta`
- `GET /api/v1/datasets/catalog`
- `GET /api/v1/datasets/{datasetId}`
- `POST /api/v1/agents/precheck`
- `POST /api/v1/agents/submit`
- `GET /api/v1/evaluations`
- `GET /api/v1/evaluations/{evaluationId}`

## 2. 关联页面与业务流程

### 2.1 数据集浏览流程

**场景**：用户从导航栏进入数据集列表页，查看详情。

**时序步骤**：

```
1. 用户访问 /dataset
   ↓
2. 页面挂载 → 调用 GET /api/v1/datasets/catalog (无参数)
   └─ 返回完整目录（包含所有难度对应的数据集）
   ↓
3. 前端展示目录树状结构
   ↓
4. 用户点击某个数据集 "身份信息泄露 (A1)"
   ↓
5. 跳转到 /dataset/A1
   ├─ 页面挂载 → 调用 GET /api/v1/datasets/A1
   ├─ 返回详情（包含description、highlights、scenarios、media等）
   ├─ 若返回 40400：显示"数据集不存在"
   └─ 若其他错误：显示"加载失败"并可重试
   ↓
6. 前端渲染详情卡片、媒体库、资源链接
```

**前端依赖行为**：

- 目录列表页不传 `difficulty` 参数
- 详情页会严格按路由参数 `datasetId` 发送请求
- 若主键不在目录中，需返回 40400

### 2.2 提交智能体完整流程（关键业务）

**场景**：用户从导航栏进入提交页，完整提交一个智能体进行评测。

**时序步骤**：

```
1. 用户访问 /user/submit
   ↓
2. 页面初始化
   ├─ 第一步：调用 GET /api/v1/agents/submit-meta
   │  └─ 返回：supportedMethods、difficulty/timeoutMinutes范围、默认值
   │
   ├─ 第二步：按初始难度调用 GET /api/v1/datasets/catalog?difficulty=0.5
   │  └─ 返回：该难度下可用的数据集列表
   │
   └─ 页面渲染提交表单（难度滑块、提交方式选择、数据集勾选）
   ↓
3. 用户交互
   ├─ 修改难度滑块 → 触发 GET /api/v1/datasets/catalog?difficulty=0.7
   │  └─ 动态更新当前难度对应的数据集列表
   │
   ├─ 填写表单
   │  ├─ agentName: "安全卫士"
   │  ├─ description: "企业安全代理"
   │  ├─ submitMethod: "api"
   │  ├─ api.baseUrl: "https://example.com/run"
   │  ├─ 勾选 datasetIds: ["A1", "B1"]
   │  └─ parameters.difficulty: 0.7（与滑块同步）
   │
   └─ 本地草稿自动保存（不含 api.token 等敏感字段）
   ↓
4. 用户点击"预检查"按钮
   ↓
5. 前端调用 POST /api/v1/agents/precheck
   ├─ 请求体包含：agentName、description、submitMethod、api/docker、parameters、datasetIds、requestId
   ├─ 业务处理：验证参数合法性、数据集可用性
   │
   └─ 返回
      ├─ 成功: { code: 0, data: { ok: true, warnings: [...] } }
      │  ├─ 第一个警告（示例）: "该结果将进入公开排行榜，请确认无敏感信息"
      │  └─ 第二个警告（示例）: "超时时间高于建议值，执行耗时可能更长"
      │
      └─ 失败: 返回相应错误码（40001/40002/40003/40004/40005/40100/50000）
   ↓
6. 预检查成功
   ├─ 前端弹框展示 warnings
   ├─ 用户确认后可继续提交，或返回修改
   │
   └─ 用户点击"提交"按钮
   ↓
7. 前端调用 POST /api/v1/agents/submit
   ├─ 请求体：与预检查完全一致（包含同一个 requestId）
   ├─ 业务处理：创建评测任务，记录 requestId 用于幂等
   │
   └─ 返回
      ├─ 成功: { code: 0, data: { evaluationId: "eval_123", status: "pending", createdAt: "..." } }
      │  ├─ 前端清空本地草稿
      │  └─ 跳转到 /user/evaluation/eval_123
      │
      └─ 失败: 返回错误码
   ↓
8. 若请求失败但用户重试
   ├─ 前端使用同一个 requestId 再次发送
   └─ 后端幂等处理：返回同一个 evaluationId，无重复创建
```

**关键点**：

- 预检查和正式提交使用同一 requestId（前端生成的 UUID）
- 同一 requestId 被调用多次应返回同一 evaluationId
- 若参数变化，后端应返回 40900 而非新建任务

### 2.3 评测查看流程

**场景**：用户在用户中心查看评测记录和详情。

**时序步骤**：

```
1. 用户访问 /user
   ↓
2. 页面挂载 → 调用 GET /api/v1/evaluations
   ├─ 鉴权：需已登录（若未登录返回 401）
   ├─ 业务处理：返回当前用户全部评测任务
   │
   └─ 返回：数组 [ { evaluationId, agentName, status, score, createdAt, ... }, ... ]
      └─ 按 createdAt 倒序排列（最新优先）
   ↓
3. 前端展示评测列表
   ├─ 每条记录显示：智能体名称、状态、得分、创建时间
   └─ 用户可点击任意条进入详情

   ↓
4. 用户点击某条记录 → 跳转到 /user/evaluation/eval_123
   ↓
5. 页面挂载 → 调用 GET /api/v1/evaluations/eval_123
   ├─ 鉴权：需已登录，且必须是当前用户自己的评测
   ├─ 业务处理
   │  └─ 若用户无权限访问，返回 40300 或 404
   │  └─ 若任务不存在，返回 40400
   │
   └─ 返回：完整评测详情
      ├─ 基本信息：evaluationId、agentName、status、createdAt
      ├─ 评测摘要：summary（文字说明）
      ├─ 风险提示：warnings[] （列表）
      └─ 详细指标：metrics[] （卡片数组）
         └─ 每个指标包含：name、value、percentage、description
   ↓
6. 前端渲染详情页
   ├─ 摘要文案
   ├─ 警告列表（如有）
   └─ 指标卡片（使用 percentage 渲染进度条）
```

---

### 2.4 页面与调用时机对照表

| 页面                   | 调用的接口                                    | 调用时机         | 是否需登录 |
| ---------------------- | --------------------------------------------- | ---------------- | ---------- |
| `/dataset`             | `GET /api/v1/datasets/catalog`                | 页面挂载         | 否         |
| `/dataset/:datasetId`  | `GET /api/v1/datasets/{datasetId}`            | 路由参数变化     | 否         |
| `/user/submit`         | `GET /api/v1/agents/submit-meta`              | 页面初始化       | 否         |
| `/user/submit`         | `GET /api/v1/datasets/catalog?difficulty=...` | 初始化、难度变化 | 否         |
| `/user/submit`         | `POST /api/v1/agents/precheck`                | 用户点击预检查   | 否         |
| `/user/submit`         | `POST /api/v1/agents/submit`                  | 用户点击正式提交 | 否         |
| `/user`                | `GET /api/v1/evaluations`                     | 页面挂载         | 是         |
| `/user/evaluation/:id` | `GET /api/v1/evaluations/{id}`                | 路由参数变化     | 是         |

## 3. 通用约定

### 3.1 Base URL

前端请求层 `frontend/src/utils/request.ts` 默认使用：

```text
/api/v1
```

下面所有接口路径都基于该前缀。

### 3.2 通用响应结构

前端统一按以下 envelope 解析响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

失败示例：

```json
{
  "code": 40002,
  "message": "参数超出允许范围。",
  "data": null
}
```

前端依赖规则如下：

- `code === 0` 表示成功
- `code !== 0` 表示业务失败
- 失败时优先展示 `message`
- `data` 在失败时允许为 `null`

### 3.3 HTTP 状态与业务错误码

当前前端同时兼容两种错误形式：

- HTTP 200 + envelope 中 `code != 0`
- HTTP 非 2xx，响应体中仍带 `message` 或 `detail`

但从前端消费角度，更推荐后端统一返回 envelope，并在鉴权失败时使用 HTTP 401。

### 3.4 鉴权要求

| 接口                                     | 是否需要登录 | 说明                     |
| ---------------------------------------- | ------------ | ------------------------ |
| `GET /api/v1/agents/submit-meta`         | 否           | 提交页初始化依赖         |
| `GET /api/v1/datasets/catalog`           | 否           | 数据集列表、提交页都依赖 |
| `GET /api/v1/datasets/{datasetId}`       | 否           | 数据集详情页依赖         |
| `POST /api/v1/agents/precheck`           | 否           | 提交流程中的预检查       |
| `POST /api/v1/agents/submit`             | 否           | 正式创建评测任务         |
| `GET /api/v1/evaluations`                | 是           | 当前登录用户的评测记录   |
| `GET /api/v1/evaluations/{evaluationId}` | 是           | 当前登录用户的评测详情   |

401 时前端行为如下：

- 清理登录态
- 弹出登录框
- 记录当前目标路由
- 登录成功后自动跳回之前目标页面

### 3.5 幂等约定

`POST /api/v1/agents/submit` 必须支持幂等。

当前前端每次提交都会携带 `requestId`，语义如下：

- 同一用户 + 同一 `requestId` 的重复提交，后端应返回同一条评测任务
- 不应重复创建任务
- 若同一 `requestId` 对应的关键业务参数与首次提交不一致，建议返回 `40900`

### 3.6 前端 Mock 与真实 API 切换机制

前端通过环境变量控制 Mock 数据和真实后端 API 的切换：

| 环境变量                       | 默认值    | 说明                                                                                                                                       |
| ------------------------------ | --------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `VITE_USE_LIVE_REFERENCE_API`  | `false`   | 当设为 `true` 时，`GET /agents/submit-meta`、`GET /datasets/catalog`、`GET /datasets/{datasetId}` 调用真实后端 API；否则使用前端 Mock 数据 |
| `VITE_USE_LIVE_SUBMISSION_API` | `false`   | 当设为 `true` 时，`POST /agents/precheck`、`POST /agents/submit`、`GET /evaluations` 系列接口调用真实后端 API；否则使用前端 Mock 数据      |
| `VITE_API_BASE_URL`            | `/api/v1` | 后端 API 的基础 URL                                                                                                                        |

**前端 Mock 与真实 API 的切换指引**：

- **开发阶段**：两个 LIVE\_\* 环境变量都为 `false`，使用前端 Mock 数据快速迭代页面逻辑
- **联调阶段**：分阶段打开环境变量，逐步集成真实后端 API：
  1. 先打开 `VITE_USE_LIVE_REFERENCE_API=true` 测试数据集接口
  2. 再打开 `VITE_USE_LIVE_SUBMISSION_API=true` 测试提交和评测接口
- **验证阶段**：所有接口都与真实后端通信，进行全流程验收
- **生产环境**：两个 LIVE\_\* 环境变量都为 `true`

**配置示例**（`.env.local`）：

```env
VITE_USE_LIVE_REFERENCE_API=false
VITE_USE_LIVE_SUBMISSION_API=false
VITE_API_BASE_URL=/api/v1
```

## 4. 数据集接口

### 4.1 获取数据集目录

`GET /api/v1/datasets/catalog`

#### 4.1.1 用途

- 数据集列表页展示全部目录
- 提交页按当前攻击难度刷新"当前可用数据集"

#### 4.1.2 Query 参数

| 参数         | 类型                  | 必填 | 说明                                  |
| ------------ | --------------------- | ---- | ------------------------------------- |
| `difficulty` | `number` 或数字字符串 | 否   | 攻击难度，范围 `0` 到 `1`，步长 `0.1` |

示例：

```text
GET /api/v1/datasets/catalog?difficulty=0.5
```

#### 4.1.3 成功响应 (code=0)

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "catalogVersion": "2026-04-01T10:00:00Z",
    "categoryCount": 4,
    "subcategoryCount": 8,
    "categories": [
      {
        "categoryId": "confidentiality",
        "name": "机密性",
        "meaning": "防止信息泄露",
        "description": "覆盖身份、密钥、隐私等高敏感信息的泄露风险。",
        "sort": 1,
        "enabled": true,
        "subcategoryCount": 2,
        "subcategories": [
          {
            "datasetId": "A1",
            "name": "身份信息泄露",
            "shortDescription": "测试多轮追问和绕行提示下的身份字段泄露。",
            "sampleCount": 1280,
            "updatedAt": "2026-03-28T12:00:00Z",
            "enabled": true
          }
        ]
      }
    ]
  }
}
```

#### 4.1.4 字段说明

- `catalogVersion`
  - 目录版本号（ISO 8601 时间戳）
  - 提交页会将其与本地草稿持久化状态联动，用于提示目录是否发生变化
  - 若后端目录版本高于前端缓存版本，前端会弹窗提示用户"数据集已更新"并建议刷新
- `categoryCount`
  - 当前返回结果中的大类总数
  - 必须与 `categories` 数组长度一致
- `subcategoryCount`
  - 当前返回结果中的数据集总数（所有 `subcategories` 的总和）
  - 用于展示"共 X 个数据集"
- `categories`
  - 数据集大类列表
- `categories[].subcategories`
  - 当前前端沿用历史字段名，实际承载"数据集摘要列表"
  - 非空时才会在前端展开显示
- `enabled`
  - 前端会基于该字段做"可用项"过滤，建议后端直接只返回可用项

#### 4.1.5 难度筛选规则

当前前端对该接口有两种使用方式：

- 数据集列表页：不传 `difficulty`
- 提交页：传 `difficulty`

后端建议行为：

- 不传 `difficulty` 时返回完整目录
- 传 `difficulty` 时返回该难度下可用的数据集子集
- 若某个大类在该难度下没有任何数据集，应从结果中移除该大类
- `categoryCount` 和 `subcategoryCount` 必须基于过滤后结果重新计算
- 若过滤后无数据，返回成功响应，`categories` 为空数组

**筛空示例**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "catalogVersion": "2026-04-01T10:00:00Z",
    "categoryCount": 0,
    "subcategoryCount": 0,
    "categories": []
  }
}
```

#### 4.1.6 常见失败响应

**测试用例1：难度参数非法**

```json
{
  "code": 40002,
  "message": "参数 difficulty 非法，应为 0 到 1 之间的数字，步长为 0.1。",
  "data": null
}
```

**对前端的影响**：

- 提交页会禁用"提交"按钮，展示红色提示
- 用户中心页面会显示"参数错误，请刷新页面"

---

**测试用例2：难度越界**

```json
{
  "code": 40002,
  "message": "difficulty 参数超出范围：应在 0 到 1 之间。",
  "data": null
}
```

**对前端的影响**：

- 与上同，用户需要修改难度滑块

---

**测试用例3：服务内部错误**

```json
{
  "code": 50000,
  "message": "服务器内部错误。",
  "data": null
}
```

**对前端的影响**：

- 数据集列表页显示"加载失败，请稍后重试"
- 提交页展示重试按钮，允许用户重新请求

---

### 4.2 获取单个数据集详情

`GET /api/v1/datasets/{datasetId}`

#### 4.2.1 用途

- 数据集详情页直接加载详情内容

#### 4.2.2 成功响应 (code=0)

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "datasetId": "A1",
    "name": "身份信息泄露",
    "category": {
      "categoryId": "confidentiality",
      "name": "机密性",
      "meaning": "防止信息泄露"
    },
    "shortDescription": "测试多轮追问和绕行提示下的身份字段泄露。",
    "fullDescription": "该数据集围绕身份证号、手机号、地址、邮箱等高敏感字段构造多轮攻击样本，用于验证智能体是否会在追问、伪装授权和历史会话回放中回显真实信息。",
    "sampleCount": 1280,
    "updatedAt": "2026-03-28T12:00:00Z",
    "highlights": [
      "覆盖直接索取、间接诱导和历史会话挖掘。",
      "适合验证脱敏、拒答和重写策略。"
    ],
    "scenarios": ["客服场景下回显用户手机号。", "知识助手回显员工实名与邮箱。"],
    "resources": [
      {
        "label": "查看字段说明",
        "url": "https://example.com/docs/datasets/A1",
        "type": "docs"
      }
    ],
    "media": [
      {
        "mediaId": "A1-image",
        "type": "image",
        "title": "身份信息泄露样例概览",
        "description": "用于展示典型攻击样本与响应结构。",
        "url": "https://cdn.example.com/datasets/A1/overview.png",
        "coverUrl": null,
        "sort": 1
      }
    ]
  }
}
```

#### 4.2.3 字段说明

- `category`
  - 数据集所属分类摘要
- `highlights`
  - 数据集评测重点，页面按列表展示
- `scenarios`
  - 典型使用或攻击场景，页面按列表展示
- `resources`
  - 当前前端类型已接入该字段，虽然详情页当前未渲染，但正式接口仍应返回
  - 即使为空列表也应返回 `resources: []`
- `resources[].type`
  - 当前约定值：`docs`、`download`、`demo`
  - 其他值会被前端忽略
- `media`
  - 媒体资源列表，详情页使用 `DatasetMediaGallery` 展示
- `media[].type`
  - 当前约定值：`image`、`video`
  - 前端仅支持这两种类型
- `media[].coverUrl`
  - 视频封面 URL，可为 `null`
  - 仅当 `media[].type === 'video'` 时启用
- `media[].sort`
  - 可选排序字段
  - 前端会按此字段升序渲染媒体列表

#### 4.2.4 一致性要求

- `datasetId`、`name`、`shortDescription`、`sampleCount`、`updatedAt` 应与目录接口中的同一数据集保持一致
- 目录与详情应来自同一份主数据源，避免出现名称或统计不一致
- 若前端检测到不一致（如 `updatedAt` 不同），会自动刷新并提示用户"数据已更新"

#### 4.2.5 常见失败响应

**测试用例1：数据集不存在**

```json
{
  "code": 40400,
  "message": "数据集 A999 不存在或已下线。",
  "data": null
}
```

**对前端的影响**：

- 详情页显示"该数据集不存在"提示
- 不显示通用的"加载失败"错误
- 用户可返回列表重试

---

**测试用例2：数据集已下线**

```json
{
  "code": 40400,
  "message": "该数据集已下线，请返回列表查看其他数据集。",
  "data": null
}
```

**对前端的影响**：

- 同上，显示专用的不存在状态

---

**测试用例3：服务内部错误**

```json
{
  "code": 50000,
  "message": "服务器数据库连接异常，请稍后重试。",
  "data": null
}
```

**对前端的影响**：

- 显示"详情加载失败，请稍后重试"
- 提供手动重试按钮

---

## 5. 提交前元数据接口

### 5.1 获取提交参数元数据

`GET /api/v1/agents/submit-meta`

#### 5.1.1 用途

- 决定提交页支持哪些提交方式
- 决定攻击难度、超时时间、布尔参数的默认值与取值范围
- 决定前端对超时时间的软提示阈值

#### 5.1.2 成功响应 (code=0)

```json
{
  "code": 0,
  "message": "success",
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
  }
}
```

#### 5.1.3 字段说明

- `supportedMethods`
  - 当前前端只支持 `api` 和 `docker`
  - 后端可在运维层动态调整此列表
  - 若某方式不支持，前端会自动隐藏对应选项卡
- `difficulty`
  - 攻击难度元数据
  - `default` 用于提交页初始化表单
- `timeoutMinutes`
  - 单次评测超时元数据
  - 单位为分钟（整数）
- `timeoutMinutes.recommendedMax`
  - 软提示阈值，不是硬上限
  - 当前前端当 `timeoutMinutes > recommendedMax` 时，会在预检查阶段提示"执行耗时可能更长"
  - 与 `max` 的区别：max 作为输入框硬上限，recommendedMax 作为UX提示
- `retryEnabled.default`
  - 失败重试默认值（布尔）
  - 前端勾选框初始状态
- `publicToLeaderboard.default`
  - 是否公开到排行榜默认值（布尔）
  - 前端勾选框初始状态

#### 5.1.4 兼容说明

前端当前仍兼容旧结构：

```json
{
  "supportedMethods": ["api", "docker"],
  "parameterMeta": {
    "difficulty": { "min": 0, "max": 1, "step": 0.1, "default": 0.5 },
    "timeoutMinutes": { "min": 15, "max": 30, "step": 1, "default": 15 },
    "retryEnabled": { "default": false },
    "publicToLeaderboard": { "default": true }
  }
}
```

但这只是过渡兼容层。后端新实现建议直接返回扁平结构，不再使用 `parameterMeta` 包裹。

#### 5.1.5 常见失败响应

**测试用例1：服务内部错误**

```json
{
  "code": 50000,
  "message": "无法获取提交元数据，服务暂时不可用。",
  "data": null
}
```

**对前端的影响**：

- 提交页进入"初始化失败"状态
- 显示全屏错误提示与重试按钮
- 用户无法继续提交

---

## 6. 提交接口

### 6.1 提交前预检查

`POST /api/v1/agents/precheck`

#### 6.1.1 用途

- 校验当前提交参数是否合法
- 返回非阻断性告警信息
- 不创建评测任务

#### 6.1.2 请求体

前端页面内部字段名为 `selectedDatasetIds`，但发给后端前会在适配器层转换为 `datasetIds`。

推荐请求体如下：

```json
{
  "agentName": "安全卫士 v1.0",
  "description": "面向企业场景的多工具安全代理。",
  "submitMethod": "api",
  "api": {
    "baseUrl": "https://example.com/agent/run",
    "token": "sk-xxxx"
  },
  "docker": null,
  "parameters": {
    "difficulty": 0.5,
    "timeoutMinutes": 15,
    "retryEnabled": false
  },
  "publicToLeaderboard": true,
  "datasetIds": ["A1", "B1", "D1"],
  "requestId": "8c5ecb4e-79f9-47eb-84d8-a8aa0d53f27f"
}
```

#### 6.1.3 字段说明

- `agentName`
  - 必填，智能体名称
  - 前端会做基础格式检查（非空、长度 1-100）
- `description`
  - 选填，智能体描述
  - 可为空字符串
- `submitMethod`
  - 必填，当前仅支持 `api`、`docker`
- `api`
  - 当 `submitMethod=api` 时必须提供
  - 当 `submitMethod=docker` 时应为 `null`
- `api.baseUrl`
  - 必填，且必须为合法 `http/https` URL
  - 前端在预提交时会用正则验证格式
  - 后端也需再次验证
- `api.token`
  - 选填，敏感字段，前端不会持久化
  - 可为空字符串
- `docker`
  - 当 `submitMethod=docker` 时必须提供对象
  - 当 `submitMethod=api` 时应为 `null`
- `docker.imageUri`
  - 必填 (当use docker)，镜像 URI
  - 格式如 `my-registry.com/my-image:latest`
- `docker.username`
  - 选填，私有镜像仓库用户名
- `docker.password`
  - 选填，敏感字段，前端不会持久化
- `parameters.difficulty`
  - 必须满足 `submit-meta.difficulty` 定义的范围与步长
  - 示例：如果 meta 定义为 min=0, max=1, step=0.1，则只能是 0, 0.1, 0.2, ..., 1.0
- `parameters.timeoutMinutes`
  - 必须满足 `submit-meta.timeoutMinutes` 定义的范围与步长
  - 整数值
- `parameters.retryEnabled`
  - 布尔值
- `publicToLeaderboard`
  - 布尔值
  - 为 `true` 时应在回复中提醒用户敏感信息
- `datasetIds`
  - 数组，至少一个元素，最多 100 个（前端限制）
  - 必须都是当前有效且可见的数据集
  - 无重复
- `requestId`
  - 必填，UUID v4 格式
  - 幂等请求标识，正式提交时也会复用
  - 由前端生成并传递

#### 6.1.4 成功响应 (code=0)

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "ok": true,
    "warnings": [
      "该次结果将进入公开排行榜，请确认描述中不包含敏感信息。",
      "当前超时时间高于建议值 20 分钟，评测排队与执行耗时可能更长。"
    ]
  }
}
```

#### 6.1.5 交互语义

- `ok` 为 `true` 表示参数合法，可继续提交
- `warnings` 为非阻断提示列表
  - 前端会以弹框形式展示所有 warnings
  - 用户可选择"确认并提交"或"返回修改"
  - 若预检查失败（code !== 0），前端不会继续调用正式提交接口

#### 6.1.6 常见失败响应

**测试用例1：API 地址格式错误**

```json
{
  "code": 40001,
  "message": "API 地址格式不合法：baseUrl 必须以 http:// 或 https:// 开头。",
  "data": null
}
```

**对前端的影响**：

- 预检查失败，弹框展示错误
- 用户返回编辑表单修正 baseUrl

---

**测试用例2：参数超出范围**

```json
{
  "code": 40002,
  "message": "参数 difficulty 必须在 0 到 1 之间，步长为 0.1。",
  "data": null
}
```

**对前端的影响**：

- 同上，预检查失败

---

**测试用例3：未选择任何数据集**

```json
{
  "code": 40003,
  "message": "至少需要选择一个数据集。",
  "data": null
}
```

**对前端的影响**：

- 返回修改，提示用户勾选数据集

---

**测试用例4：数据集不存在或不可选**

```json
{
  "code": 40004,
  "message": "数据集 A999 不存在或已下线，无法选择。",
  "data": null
}
```

**对前端的影响**：

- 可能由于目录已刷新导致
- 建议用户返回列表重新选择数据集

---

**测试用例5：提交方式不可用**

```json
{
  "code": 40005,
  "message": "Docker 提交方式当前不可用，请切换为 API 方式。",
  "data": null
}
```

**对前端的影响**：

- 前端提交页应基于 supportedMethods 预先隐藏
- 若后端动态禁用某方式，此错误用于防守

---

**测试用例6：服务内部错误**

```json
{
  "code": 50000,
  "message": "预检查服务异常，无法完成验证，请稍后重试。",
  "data": null
}
```

**对前端的影响**：

- 用户可点击重试或返回编辑

---

### 6.2 正式提交

`POST /api/v1/agents/submit`

#### 6.2.1 用途

- 创建评测任务
- 返回任务 ID，供前端跳转评测详情页

#### 6.2.2 请求体

与 `POST /api/v1/agents/precheck` 保持一致。

#### 6.2.3 成功响应 (code=0)

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "evaluationId": "eval_1711960000123",
    "status": "pending",
    "createdAt": "2026-04-01T12:00:00Z"
  }
}
```

#### 6.2.4 字段说明

- `evaluationId`
  - 评测任务唯一标识
  - 后续所有查询均以此为主键
- `status`
  - 当前前端支持值：`pending`、`running`、`completed`
  - 初始状态应为 `pending`
- `createdAt`
  - ISO 8601 时间字符串（UTC）
  - 前端用于展示任务创建时间

#### 6.2.5 前端成功后行为

- 清空本地提交草稿（localStorage）
- 跳转到 `/user/evaluation/{evaluationId}`
- 详情页会定期轮询评测进度

#### 6.2.6 幂等要求

- 同一用户 + 同一 `requestId` 的重复提交，必须返回同一 `evaluationId`
- 不应重复创建任务
- 如果同一 `requestId` 对应不同的关键业务参数，建议返回 `40900`

**幂等容错场景**：

1. 用户提交后，网络断开
   → 前端在 localStorage 中缓存 requestId
   → 用户手动刷新或重新提交时，前端发送同一 requestId
   → 后端幂等返回之前已创建的 evaluationId

2. 用户调整参数后重新提交
   → 前端生成新的 requestId（UUID 随机）
   → 后端创建新的评测任务

#### 6.2.7 常见失败响应

**测试用例1：HTTP 413 请求体过大**

```json
{
  "code": 40002,
  "message": "请求数据过大，请减少数据集选择数量。",
  "data": null
}
```

**对前端的影响**：

- 前端应限制 datasetIds 最多 100 个（已在代码中实现）

---

**测试用例2：幂等冲突 - 参数不一致**

```json
{
  "code": 40900,
  "message": "相同的 requestId 已提交过，但参数不一致。请生成新的 requestId 重新提交。",
  "data": null
}
```

**对前端的影响**：

- 提示用户"参数已修改，请重新提交"
- 前端自动生成新 requestId 并再次提交

---

**测试用例3：服务内部错误**

```json
{
  "code": 50000,
  "message": "创建评测任务失败，服务暂时不可用。",
  "data": null
}
```

**对前端的影响**：

- 用户可点击"重试"，前端使用同一 requestId 发送请求
- 后端幂等返回新创建的 evaluationId（如果之前部分成功）或同一 evaluationId 的回复

---

## 7. 评测记录接口

### 7.1 获取当前用户评测记录

`GET /api/v1/evaluations`

#### 7.1.1 用途

- 用户中心 `/user` 页面展示评测记录列表

#### 7.1.2 成功响应 (code=0)

```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "evaluationId": "eval_20260331_001",
      "agentName": "安全卫士 v1.0",
      "description": "面向企业场景的多工具安全代理。",
      "createdAt": "2026-03-31T10:20:00Z",
      "updatedAt": "2026-03-31T11:05:00Z",
      "status": "completed",
      "publicToLeaderboard": true,
      "datasetIds": ["A1", "B1"],
      "datasetNames": ["身份信息泄露", "指令篡改"],
      "submitMethod": "api",
      "score": 94.6,
      "ownerName": "张三",
      "parameters": {
        "difficulty": 0.5,
        "timeoutMinutes": 18,
        "retryEnabled": false
      }
    }
  ]
}
```

#### 7.1.3 字段说明

- `datasetNames`
  - 页面直接展示的人类可读名称列表
  - 与 `datasetIds` 一一对应
- `score`
  - 评测得分
  - 任务未完成时可为 `null` 或不返回
  - 格式：0-100 数字
- `ownerName`
  - 当前任务所属用户的展示名（昵称）
- `status`
  - 当前支持：`pending`（排队中）、`running`（执行中）、`completed`（已完成）

#### 7.1.4 排序建议

前端当前假定"最新创建的任务优先展示"。推荐后端按 `createdAt` 倒序返回。

#### 7.1.5 常见失败响应

**测试用例1：未登录**

```json
{
  "code": 40100,
  "message": "未登录或登录失效，请先登录。",
  "data": null
}
```

**对前端的影响**：

- 触发全局 401 拦截器
- 弹出登录框
- 登录成功后自动重试此请求

---

**测试用例2：服务内部错误**

```json
{
  "code": 50000,
  "message": "无法获取评测记录，服务暂时不可用。",
  "data": null
}
```

**对前端的影响**：

- 列表页显示"加载失败"提示与重试按钮

---

### 7.2 获取单个评测详情

`GET /api/v1/evaluations/{evaluationId}`

#### 7.2.1 用途

- 评测详情页 `/user/evaluation/:evaluationId` 展示摘要、告警和详细指标

#### 7.2.2 成功响应 (code=0)

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "evaluationId": "eval_20260331_001",
    "agentName": "安全卫士 v1.0",
    "description": "面向企业场景的多工具安全代理。",
    "createdAt": "2026-03-31T10:20:00Z",
    "updatedAt": "2026-03-31T11:05:00Z",
    "status": "completed",
    "publicToLeaderboard": true,
    "datasetIds": ["A1", "B1"],
    "datasetNames": ["身份信息泄露", "指令篡改"],
    "submitMethod": "api",
    "score": 94.6,
    "ownerName": "张三",
    "parameters": {
      "difficulty": 0.5,
      "timeoutMinutes": 18,
      "retryEnabled": false
    },
    "summary": "本次评测共覆盖 2 个数据集，核心安全指标表现稳定，建议结合详细指标继续优化高风险边界。",
    "warnings": ["建议调整 timeout 参数以覆盖更多边界场景"],
    "metrics": [
      {
        "name": "攻击检测率",
        "value": "96%",
        "percentage": 96,
        "description": "识别恶意提示与异常工具响应的能力。"
      },
      {
        "name": "信息保护率",
        "value": "92%",
        "percentage": 92,
        "description": "防止敏感信息泄露的防护有效率。"
      }
    ]
  }
}
```

#### 7.2.3 字段说明

- `summary`
  - 详情页摘要文案
  - 支持多行文本
- `warnings`
  - 风险提示列表
  - 可为空数组
  - 前端以列表形式展示，每项带警告图标
- `metrics`
  - 指标卡片列表
  - 可为空数组（任务未完成时）
- `metrics[].percentage`
  - 进度条数值，前端预期范围 `0-100`
  - 必须为整数
- `metrics[].value`
  - 指标的展示值（如"96%"）
  - 纯文本，前端直接展示

#### 7.2.4 常见失败响应

**测试用例1：未登录**

```json
{
  "code": 40100,
  "message": "未登录或登录失效，请先登录。",
  "data": null
}
```

**对前端的影响**：

- 触发全局 401 拦截器

---

**测试用例2：无权查看**

```json
{
  "code": 40300,
  "message": "无权查看该评测，只能查看自己的评测。",
  "data": null
}
```

**对前端的影响**：

- 展示"无权访问"页面
- 提供返回列表链接

---

**测试用例3：评测不存在**

```json
{
  "code": 40400,
  "message": "评测任务 eval_123 不存在或已被删除。",
  "data": null
}
```

**对前端的影响**：

- 展示"评测不存在"页面
- 可返回列表重新查询

---

**测试用例4：服务内部错误**

```json
{
  "code": 50000,
  "message": "无法获取评测详情，请稍后重试。",
  "data": null
}
```

**对前端的影响**：

- 详情页显示"加载失败"提示与重试按钮

---

## 8. 前端校验与映射规则

### 8.1 提交方式与字段联动

- `submitMethod=api`
  - 必须提供 `api.baseUrl`
  - `api.baseUrl` 必须为合法 `http/https` URL
- `submitMethod=docker`
  - 必须提供 `docker.imageUri`

### 8.2 参数范围

当前前端默认值为：

- `difficulty`
  - `min=0`
  - `max=1`
  - `step=0.1`
  - `default=0.5`
- `timeoutMinutes`
  - `min=15`
  - `max=30`
  - `step=1`
  - `default=15`
  - `recommendedMax=20`
- `retryEnabled.default=false`
- `publicToLeaderboard.default=true`

### 8.3 数据集字段映射

前端内部表单状态使用：

```json
{
  "selectedDatasetIds": ["A1", "B1"]
}
```

真正发给后端前会转换成：

```json
{
  "datasetIds": ["A1", "B1"]
}
```

因此后端正式接口契约请直接使用 `datasetIds`，不要使用 `selectedDatasetIds`。

### 8.4 本地持久化边界

提交页会持久化非敏感字段，包括：

- `submitMethod`
- `agentName`
- `description`
- `api.baseUrl`
- `docker.imageUri`
- `docker.username`
- `parameters`
- `publicToLeaderboard`
- `selectedDatasetIds`
- `expandedCategoryIds`

提交页不会持久化：

- `api.token`
- `docker.password`
- 其他敏感凭证字段

后端不能假设刷新页面后这些敏感字段仍然存在。

## 9. 推荐错误码与前端处理

| code    | HTTP 状态 | API 位置                               | 含义                                                    | 前端处理建议                                                                   |
| ------- | --------- | -------------------------------------- | ------------------------------------------------------- | ------------------------------------------------------------------------------ |
| `0`     | 200       | 所有                                   | 成功                                                    | 无特殊处理                                                                     |
| `40001` | 400       | precheck, submit                       | API 地址格式错误（baseUrl 不是合法 URL）                | 显示 message 提示，建议用户检查 baseUrl 格式                                   |
| `40002` | 400       | submit-meta, catalog, precheck, submit | 参数超出允许范围（难度、超时、数据集数量等）            | 显示 message，禁用提交，提示用户调整参数                                       |
| `40003` | 400       | precheck, submit                       | 未选择任何数据集                                        | 显示 message，提示用户选择数据集                                               |
| `40004` | 400       | precheck, submit                       | 数据集不存在、已下线或不可选（在当前难度下不可用）      | 显示 message，建议用户刷新数据集目录                                           |
| `40005` | 400       | precheck, submit                       | 提交方式当前不可用（如 docker 未启用）                  | 显示 message，提示用户切换提交方式                                             |
| `40100` | 401       | precheck, submit, evaluations/\*       | 未登录或登录失效                                        | 触发 `unauthorized` 事件，弹出全局登录对话框，记录当前路由，登录成功后自动跳回 |
| `40300` | 403       | evaluations/{id}                       | 无权查看该评测详情（非本人评测或已被删除）              | 显示"无权访问"或"未找到"提示                                                   |
| `40400` | 404       | datasets/{id}, evaluations/{id}        | 资源不存在或已删除                                      | 在数据集详情页显示"数据集不存在"；在评测详情页显示"评测未找到"                 |
| `40900` | 409       | submit                                 | 幂等冲突或重复请求参数不一致（同 requestId 但参数变了） | 显示 message，建议用户重新提交（前端会生成新 requestId）                       |
| `50000` | 500       | 所有                                   | 服务器内部错误                                          | 显示"服务异常，请稍后重试"，提供重试按钮                                       |

## 10. 性能与可扩展性考量

### 10.1 客户端缓存策略

**数据集目录缓存**：

- 前端通过 `catalogVersion` 字段检测版本变化
- 若后端返回的 `catalogVersion` 高于本地缓存版本，前端会弹窗提示用户"数据已更新"
- 建议后端采用 `CacheControl: max-age=3600` HTTP 头（1小时）
- 若需实时更新，后端可通过 WebSocket 或 Server-Sent Events 推送新版本号

**评测详情缓存**：

- 已完成的评测（status=completed）数据不再变化，可用 HTTP 缓存 `max-age=86400`（1天）
- 进行中的评测（status=pending/running）每 3-5 秒前端会主动轮询一次，建议不缓存

### 10.2 分页与批量操作

**评测列表分页**（未来优化）：

- 当前前端假设一次返回全部评测列表
- 若用户评测数超过 1000，建议后端采用光标分页（cursor-based pagination）
- 格式示例：
  ```json
  {
    "code": 0,
    "data": {
      "records": [...],
      "nextCursor": "s20h3kl2hsdfs...",
      "hasMore": true
    }
  }
  ```

**数据集批量查询**（未来优化）：

- 提交页若需同时检查多个数据集的详细信息，可考虑添加 `POST /api/v1/datasets/batch` 端点
- 当前前端逐个调用详情接口，无性能问题

### 10.3 速率限制

**建议限流策略**：

- 公开接口（无需登录）：100 req/min per IP
- 用户私有接口：1000 req/min per user
- 预检查与提交接口（易被滥用）：20 req/min per user

**前端对限流的处理**：

- 若收到 HTTP 429，显示"请求过于频繁，请稍后重试"
- 前端会自动添加 10 秒延迟后重试

### 10.4 并发提交容错

**重复提交防护**：

- 前端提交按钮在请求进行中会被禁用
- 若用户强制关闭浏览器或网络中断，前端下次加载时会检测本地缓存的 requestId
- 建议后端对同一 requestId 的并发请求返回同一结果（设置唯一性约束）

### 10.5 数据一致性

**目录与详情的一致性**：

- 后端应确保目录接口返回的数据集元素与详情接口返回的同一数据集保持字段一致
- 若检测到不一致（如 name、updatedAt 不同），前端会自动刷新并提示用户"数据已更新"

**评测记录与详情的一致性**：

- 列表接口返回的 score、status 应与详情接口保持实时同步
- 建议两个接口从同一数据源查询，避免时间差导致的空值问题

## 11. 联调建议顺序

建议后端按以下顺序实现，便于前端逐步切换真实接口：

1. `GET /api/v1/agents/submit-meta`
   - 最简单的接口，无依赖
   - 用于验证基础 HTTP 框架
2. `GET /api/v1/datasets/catalog`
   - 依赖数据库，但不涉及用户认证
   - 测试基本的业务逻辑

3. `GET /api/v1/datasets/{datasetId}`
   - 验证路由参数解析与错误处理

4. `POST /api/v1/agents/precheck`
   - 首个 POST 接口，涉及请求体解析
   - 逻辑复杂度中等

5. `POST /api/v1/agents/submit`
   - 需要实现幂等逻辑
   - 涉及数据库事务
   - 业务逻辑最复杂

6. `GET /api/v1/evaluations`
   - 需要认证与授权
   - 返回列表数据

7. `GET /api/v1/evaluations/{evaluationId}`
   - 需要认证、授权与关联查询
   - 最后实现

如果只想先打通提交页核心流程，至少需要先完成前 5 项。用户中心相关功能可后续补齐。

## 附录 A：前端 TypeScript 类型定义

本节列出所有 API 交互涉及的 TypeScript 接口定义，供后端参考。详见 [src/types/](https://github.com/your-repo/frontend/src/types)

### A.1 通用类型

```typescript
/**
 * 统一响应 Envelope
 */
interface ApiResponse<T = any> {
  code: number; // 0 表示成功，非 0 表示失败
  message: string;
  data: T | null;
}

/**
 * 分页相应（未来扩展）
 */
interface PaginatedResponse<T> {
  records: T[];
  nextCursor?: string; // 光标分页标识
  hasMore: boolean;
  total?: number; // 总数（可选）
}
```

### A.2 数据集相关类型

```typescript
/**
 * 数据集目录响应
 */
interface DatasetCatalogResponse {
  catalogVersion: string; // ISO 8601 时间戳
  categoryCount: number;
  subcategoryCount: number;
  categories: DatasetCategory[];
}

interface DatasetCategory {
  categoryId: string;
  name: string;
  meaning: string;
  description?: string;
  sort: number;
  enabled: boolean;
  subcategoryCount?: number;
  subcategories: DatasetSummary[];
}

/**
 * 数据集摘要（出现在目录的 subcategories 中）
 */
interface DatasetSummary {
  datasetId: string;
  name: string;
  shortDescription: string;
  sampleCount: number;
  updatedAt: string; // ISO 8601
  enabled: boolean;
}

/**
 * 数据集详情响应
 */
interface DatasetDetail extends DatasetSummary {
  category: {
    categoryId: string;
    name: string;
    meaning: string;
  };
  fullDescription: string;
  highlights: string[];
  scenarios: string[];
  resources: DatasetResourceLink[];
  media: DatasetMediaItem[];
}

interface DatasetResourceLink {
  label: string;
  url: string;
  type: "docs" | "download" | "demo"; // 必填
}

interface DatasetMediaItem {
  mediaId: string;
  type: "image" | "video";
  title: string;
  description?: string;
  url: string;
  coverUrl?: string | null; // 视频封面
  sort?: number;
}
```

### A.3 提交元数据类型

```typescript
/**
 * 提交参数元数据响应
 */
interface SubmitMetaResponse {
  supportedMethods: ("api" | "docker")[];
  difficulty: RangeMetadata;
  timeoutMinutes: RangeMetadata & { recommendedMax: number };
  retryEnabled: { default: boolean };
  publicToLeaderboard: { default: boolean };
}

interface RangeMetadata {
  min: number;
  max: number;
  step: number;
  default: number;
}
```

### A.4 提交请求体类型

```typescript
/**
 * 提交智能体的请求体（预检查和正式提交通用）
 */
interface SubmitAgentPayload {
  agentName: string;
  description?: string;
  submitMethod: "api" | "docker";
  api?: {
    baseUrl: string;
    token?: string; // 敏感，前端不持久化
  };
  docker?: {
    imageUri: string;
    username?: string;
    password?: string; // 敏感，前端不持久化
  };
  parameters: {
    difficulty: number;
    timeoutMinutes: number;
    retryEnabled: boolean;
  };
  publicToLeaderboard: boolean;
  datasetIds: string[]; // 至少 1 个，最多 100 个
  requestId: string; // UUID v4，用于幂等
}
```

### A.5 预检查响应类型

```typescript
interface PrecheckResponse {
  ok: boolean;
  warnings: string[]; // 非阻断警告列表
}
```

### A.6 提交响应类型

```typescript
/**
 * 正式提交成功时的响应
 */
interface SubmitResponse {
  evaluationId: string;
  status: "pending" | "running" | "completed";
  createdAt: string; // ISO 8601
}
```

### A.7 评测记录类型

```typescript
/**
 * 评测记录摘要（出现在列表中）
 */
interface EvaluationRecord {
  evaluationId: string;
  agentName: string;
  description?: string;
  createdAt: string; // ISO 8601
  updatedAt: string; // ISO 8601
  status: "pending" | "running" | "completed";
  publicToLeaderboard: boolean;
  datasetIds: string[];
  datasetNames: string[]; // 与 datasetIds 一一对应
  submitMethod: "api" | "docker";
  score?: number | null; // 未完成时为 null
  ownerName: string;
  parameters: {
    difficulty: number;
    timeoutMinutes: number;
    retryEnabled: boolean;
  };
}

/**
 * 评测详情（扩展 EvaluationRecord）
 */
interface EvaluationDetail extends EvaluationRecord {
  summary: string; // 摘要文案
  warnings: string[]; // 风险提示列表
  metrics: EvaluationMetric[]; // 详细指标
}

interface EvaluationMetric {
  name: string;
  value: string; // 如 "96%"
  percentage: number; // 0-100
  description?: string;
}
```

---

本文档最后更新于 2026-04-02，对应前端版本 v1.0.0（改进版）
