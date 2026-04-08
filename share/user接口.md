# 用户接口

## 1. 文档目标

本文档定义当前前后端已经对齐的用户相关接口契约。
对应后端实现位于：

- `backend/app/api/v1/endpoints/auth.py`
- `backend/app/api/v1/endpoints/user.py`

统一响应与错误码主表见 [backend/docs/05-规范/响应与错误码约定.md](../backend/docs/05-规范/响应与错误码约定.md)。

## 2. 通用约定

- Base URL：`/api/v1`
- 除头像上传接口外，请求与响应均使用 JSON
- 除注册、登录外，其余接口需携带 `Authorization: Bearer <token>`
- 业务成功与业务失败统一返回 `{ code, data, message }`

兼容性说明：

- 当前业务层错误已统一返回 `{ code, data, message }`
- 请求体结构错误、字段类型错误、部分 schema 校验错误目前仍可能返回 FastAPI/Pydantic 默认 `422` 响应，前端不应把它误当成业务成功

## 3. 接口列表

### 3.1 用户登录

- 路由：`POST /api/v1/auth/login`
- 说明：支持用户名或邮箱登录

请求体示例：

```json
{
  "username": "alice",
  "password": "123456"
}
```

成功响应示例：

```json
{
  "code": 0,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "user": {
      "id": 1,
      "username": "alice",
      "email": "alice@example.com",
      "avatarUrl": null
    }
  },
  "message": "success"
}
```

业务失败示例：

- 用户名或密码错误：`401` + `{"code":1001,"data":null,"message":"用户名或密码错误"}`
- 用户名仅包含空白字符：`400` + `{"code":1000,"data":null,"message":"用户名和密码不能为空"}`

### 3.2 用户注册

- 路由：`POST /api/v1/auth/register`
- 说明：注册成功后直接返回 token 与用户信息

请求体示例：

```json
{
  "username": "alice",
  "email": "alice@example.com",
  "password": "123456"
}
```

成功响应示例：

```json
{
  "code": 0,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "user": {
      "id": 1,
      "username": "alice",
      "email": "alice@example.com",
      "avatarUrl": null
    }
  },
  "message": "success"
}
```

业务失败示例：

- 用户名已被注册：`409` + `{"code":1002,"data":null,"message":"用户名已被注册"}`
- 邮箱已被注册：`409` + `{"code":1002,"data":null,"message":"邮箱已被注册"}`

### 3.3 当前用户

- 路由：`GET /api/v1/auth/me`
- 鉴权：需要

请求头示例：

```http
Authorization: Bearer <token>
```

成功响应示例：

```json
{
  "code": 0,
  "data": {
    "id": 1,
    "username": "alice",
    "email": "alice@example.com",
    "avatarUrl": "/uploads/avatars/1_xxx.png"
  },
  "message": "success"
}
```

业务失败示例：

- 未登录：`401` + `{"code":401,"data":null,"message":"未授权，请先登录"}`
- token 无效或已过期：`401` + `{"code":401,"data":null,"message":"token 无效或已过期"}`

### 3.4 获取用户资料

- 路由：`GET /api/v1/user/profile`
- 鉴权：需要
- 说明：当前与 `GET /api/v1/auth/me` 返回结构一致

成功响应示例：

```json
{
  "code": 0,
  "data": {
    "id": 1,
    "username": "alice",
    "email": "alice@example.com",
    "avatarUrl": "/uploads/avatars/1_xxx.png"
  },
  "message": "success"
}
```

### 3.5 修改用户资料

- 路由：`PUT /api/v1/user/profile`
- 鉴权：需要
- 说明：当前允许修改 `username` 和 `password`，不允许修改 `email`

请求体示例：

```json
{
  "username": "alice_new",
  "password": "654321"
}
```

成功响应示例：

```json
{
  "code": 0,
  "data": {
    "id": 1,
    "username": "alice_new",
    "email": "alice@example.com",
    "avatarUrl": "/uploads/avatars/1_xxx.png"
  },
  "message": "success"
}
```

业务失败示例：

- 用户名已被占用：`409` + `{"code":1003,"data":null,"message":"用户名已被占用"}`
- 没有提供可修改字段：`400` + `{"code":1000,"data":null,"message":"没有提供要修改的字段"}`
- 尝试修改邮箱：`403` + `{"code":1004,"data":null,"message":"邮箱不可修改"}`
- 未登录或 token 无效：同 `GET /api/v1/auth/me`

### 3.6 上传头像

- 路由：`POST /api/v1/user/avatar`
- 鉴权：需要
- 请求类型：`multipart/form-data`
- 表单字段：`avatar`

请求示例：

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/user/avatar" \
  -H "Authorization: Bearer <token>" \
  -F "avatar=@./avatar.png"
```

成功响应示例：

```json
{
  "code": 0,
  "data": {
    "avatarUrl": "/uploads/avatars/1_2f6ab0d8f3d44b9d9c0b55f2a62d23d0.png"
  },
  "message": "success"
}
```

业务失败示例：

- 未上传文件：`400` + `{"code":1000,"data":null,"message":"请选择要上传的头像"}`
- 文件类型不支持：`400` + `{"code":1000,"data":null,"message":"仅支持 JPG、PNG 格式"}`
- 文件大小超过 2MB：`400` + `{"code":1000,"data":null,"message":"头像大小不能超过 2MB"}`
- 上传失败：`500` + `{"code":500,"data":null,"message":"头像上传失败，请稍后重试"}`
