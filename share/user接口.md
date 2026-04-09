# 用户接口补充说明

> 本文档是 [`API接口协议.md`](./API接口协议.md) 的用户域补充说明。  
> 精确路由、请求体、响应体和错误码以总协议为准。

## 1. 后端实现入口

- `backend/app/modules/auth/router.py`
- `backend/app/modules/user/router.py`

## 2. 当前覆盖接口

- `POST /api/v1/auth/login`
- `POST /api/v1/auth/register`
- `GET /api/v1/auth/me`
- `GET /api/v1/user/profile`
- `PUT /api/v1/user/profile`
- `POST /api/v1/user/avatar`

## 3. 领域补充约定

- 登录支持用户名或邮箱作为登录标识。
- 注册成功后直接返回 token 与当前用户资料。
- `GET /api/v1/auth/me` 与 `GET /api/v1/user/profile` 当前返回同一份用户展示结构。
- `PUT /api/v1/user/profile` 当前允许修改 `username`、`password`，明确不允许修改 `email`。
- `POST /api/v1/user/avatar` 使用 `multipart/form-data`，字段名固定为 `avatar`。
- 请求参数校验失败也会返回 envelope，错误码为 `1000`，不再使用 FastAPI 默认裸 `422` 结构。
- 需要登录的用户接口统一使用 `40100 / 未登录或登录已失效。`
