# 数据集与评测流程接口说明

本文档描述当前前端在数据集浏览与提交流程中的真实调用行为，并同步补充当前页面呈现规则。

## 运行模式

由 `VITE_ENABLE_API_MOCK` 统一控制：

- `false`: 调用真实后端接口。
- `true`: 数据集、评测校验、评测创建统一走前端 mock 实现。

前端不再区分旧的“局部 live / 局部 mock”开关，也不再维护提交草稿的 localStorage 持久化版本。

## 数据集接口

### 1. 获取数据集目录

- 方法：`GET /datasets/catalog`
- 前端入口：`getDatasetCatalog(options?)`
- 支持参数：
  - `signal?: AbortSignal`
  - `force?: boolean`

前端行为：

- 默认走内存缓存。
- `force=true` 时绕过缓存重新请求。
- 数据集目录页与提交页共享同一目录资源来源，提交页刷新目录时也会透传 `force`。

### 2. 获取数据集详情

- 方法：`GET /datasets/{datasetId}`
- 前端入口：`getDatasetDetail(datasetId, options?)`
- 支持参数：
  - `signal?: AbortSignal`
  - `force?: boolean`

前端行为：

- 默认走内存缓存。
- 详情页主动刷新时会透传 `force=true`。
- 请求前会先做 `datasetId` 规范化。

## 评测流程接口

旧提交接口 `/agents/submit-meta`、`/agents/precheck`、`/agents/submit` 已移除。当前真实流程先注册并验证 Agent，再创建评测任务。

### 1. 注册或选择 Agent

- 方法：`POST /agents`、`GET /agents`、`POST /agents/{agentId}/verify`
- 前端入口：Agent 注册、列表、验证相关 API

前端行为：

- 创建 Agent 时提交运行配置和鉴权配置。
- 详情与列表接口不会返回明文凭据。
- 只有可提交评测的 Agent 才进入评测创建流程。

### 2. 获取评测提交元数据

- 方法：`GET /evaluations/meta`
- 前端入口：`getSubmitMeta()`

返回内容用于控制：

- 支持的提交方式
- 难度范围
- 超时时间范围
- 最大步数范围
- 是否默认公开到排行榜

### 3. 提交前校验

- 方法：`POST /evaluations/validate`
- 前端入口：`precheckAgent(payload)`

前端行为：

- 点击“提交任务”后先构建 payload，再做字段校验。
- 校验通过后调用评测校验接口。
- 返回的 warning 只用于确认弹窗提示，不会写入本地持久化。

### 4. 创建评测任务

- 方法：`POST /evaluations`
- 前端入口：`submitAgent(payload)`

前端行为：

- 最终提交使用与校验一致的业务 payload。
- `requestId` 在前端生成，用于当前会话内避免重复提交。
- 提交成功后清空当前页面内存中的草稿状态。

## 提交页状态边界

### 当前只保留在页面内存中的内容

- 智能体表单内容
- 已选数据集
- 展开中的分类
- 当前待提交请求信息

### 不再写入 durable localStorage 的内容

- 提交草稿
- 数据集选择草稿
- 提交预检结果
- 提交成功结果

## localStorage 仍会用到的键

- 用户 token
- 登录后跳转地址
- 会话滚动位置
- mock 评测记录（仅 mock 模式）

## 页面呈现补充

### 数据集详情页

- 第二个卡片“准备发起评测”中的标题、说明与按钮使用居中对齐。
- 该卡片只承担从详情进入提交页的明确入口，不附带额外说明性噪音文案。

### 提交评测页

- API Token 字段说明已改为更面向用户的提示文案，不再使用“仅保存在当前页面内存……”这类开发者导向措辞。
- 当目录刷新后移除了失效的数据集或展开状态时，页面内部会静默同步，不再显示左右两侧的黄色提示条。
- 目录同步仍然真实发生，只是改为不打断用户的页面操作。
