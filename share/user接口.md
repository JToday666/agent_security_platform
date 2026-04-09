# 用户接口补充说明

## 当前有效行为

本文件补充说明前端当前对认证和用户资料接口的消费方式。

### 默认真实后端

默认情况下，以下接口全部走真实后端：

- `POST /api/v1/auth/login`
- `POST /api/v1/auth/register`
- `GET /api/v1/auth/me`
- `GET /api/v1/user/profile`
- `PUT /api/v1/user/profile`
- `POST /api/v1/user/avatar`

本轮未引入新的 auth mock。

## 前端状态管理约束

### 用户资料以内存态为准

前端当前以运行时内存态作为用户资料真相源，不再把资料快照写入 localStorage 并当作长期真相。

### localStorage 允许范围

允许写入：

- token
- 登录回跳地址
- 提交草稿
- 纯 UI 状态

不再写入：

- 用户资料快照
- 评测结果快照
- 提交结果快照

## 错误处理

前端请求层当前优先按统一 envelope 解析：

- `message`
- `data.errors[]`

`detail` 只保留兼容兜底，不再作为主路径。

### 未登录处理

当后端返回未登录状态时：

- 前端统一触发未授权事件
- 清理当前登录态
- 保留登录后回跳地址
- 打开登录弹窗

## 头像与资料显示

- 头像 URL 统一做 API 资源地址归一化
- `avatarUrl`、`username`、`email` 为空时，页面必须有安全降级显示
- 不允许空字段导致页面崩溃或直接显示 `undefined`
