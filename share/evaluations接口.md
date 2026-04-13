# 评测接口说明

本文档描述当前前端在评测记录、评测详情和任务动作中的真实调用行为，并同步补充当前页面展示规则。

## 运行模式

由 `VITE_ENABLE_API_MOCK` 统一控制：

- `false`: 调用真实后端评测接口。
- `true`: 调用前端 mock 评测实现，并允许在 localStorage 中保存 mock 评测记录。

## 接口列表

### 1. 获取评测记录列表

- 方法：`GET /evaluations`
- 前端入口：`getEvaluationRecords()`

前端行为：

- 不做 durable 本地缓存。
- 仅在页面加载时请求，筛选行为在前端本地完成。
- 返回结果会先经过前端适配与脱敏整理后再进入页面。

### 2. 获取评测详情

- 方法：`GET /evaluations/{evaluationId}`
- 前端入口：`getEvaluationDetail(evaluationId)`

前端行为：

- 详情页首次进入会主动加载。
- 非终态任务会继续按页面逻辑轮询或在动作后刷新。
- 返回结果会先经过前端适配，再统一计算可用动作、进度文案和报告展示状态。

### 3. 提交任务动作

- 方法：`POST /evaluations/{evaluationId}/actions`
- 前端入口：`postEvaluationAction(evaluationId, action)`
- `action` 取值：
  - `pause`
  - `resume`
  - `terminate`
  - `cancel`

前端动作规则：

- `pause`: 仅运行中且未使用过暂停机会时允许。
- `resume`: 仅暂停中允许。
- `terminate`: 运行中或暂停中允许。
- `cancel`: 排队中、运行中、暂停中允许。

前端已将这些规则收口到共享模型逻辑，mock 存储与详情视图共用同一套判断。

## 报告展示规则

前端报告区遵循以下边界：

- 只有后端或 mock 返回最终报告后，才展示报告摘要和指标。
- 只有 `finalReportAvailable=true` 且 `score` 为数字时，才展示综合得分。
- 记录页不直接做报告分数字段格式化输出，只负责筛选与列表展示。

### 当前详情页摘要区规则

- 顶部摘要模块中，任务状态、提交方式、报告状态使用图标标记承载视觉状态，不再在彩色标记中重复展示相同文字。
- 数据集数量卡片只展示数量本身，不再在同一卡片中列出具体数据集名称。
- 具体数据集名称如需展示，应由更下层的数据或报告内容承担，不在顶部摘要区重复堆叠。

## mock 持久化边界

仅在 `VITE_ENABLE_API_MOCK=true` 时：

- mock 评测记录会写入 localStorage。
- 真实后端模式下，评测记录与详情不写入 durable localStorage。

## 页面状态

当前评测页统一使用共享页面状态卡与提示组件处理：

- 加载中
- 请求失败
- 空列表 / 无匹配结果
- 行动后的错误提示
