# 用户及认证接口协议

## 1. 用户登录

`POST /api/v1/auth/login`

### 请求体

```json
{
  "username": "user1",
  "password": "password123"
}
```

### 成功响应

```json
{
  "code": 0,
  "data": {
    "token": "eyJhbGci...",
    "user": {
      "id": 1,
      "username": "user1",
      "email": "user1@example.com",
      "avatarUrl": null
    }
  },
  "message": "success"
}
```

## 2. 用户注册

`POST /api/v1/auth/register`

### 请求体

```json
{
  "username": "user1",
  "email": "user1@example.com",
  "password": "password123"
}
```

### 成功响应

```json
{
  "code": 0,
  "data": {
    "token": "eyJhbGci...",
    "user": {
      "id": 2,
      "username": "user1",
      "email": "user1@example.com",
      "avatarUrl": null
    }
  },
  "message": "success"
}
```

## 3. 获取当前登录用户

`GET /api/v1/auth/me`

### 成功响应

```json
{
  "code": 0,
  "data": {
    "id": 1,
    "username": "user1",
    "email": "user1@example.com",
    "avatarUrl": "/uploads/avatars/1_demo.png"
  },
  "message": "success"
}
```

## 4. 获取个人资料

`GET /api/v1/user/profile`

### 说明

该接口返回与 `GET /api/v1/auth/me` 相同的用户资料快照，供个人资料页初始化使用。

### 成功响应

```json
{
  "code": 0,
  "data": {
    "id": 1,
    "username": "user1",
    "email": "user1@example.com",
    "avatarUrl": "/uploads/avatars/1_demo.png"
  },
  "message": "success"
}
```

## 5. 更新个人资料

`PUT /api/v1/user/profile`

### 请求体

```json
{
  "username": "new_user1",
  "password": "new_password123",
  "email": "user1@example.com"
}
```

### 说明

- `username` 和 `password` 当前可修改
- `email` 字段在请求模型中保留，但后端会拒绝修改，返回 `code = 1004`
- 请求体至少需要提供 `username` 或 `password` 之一

### 成功响应

```json
{
  "code": 0,
  "data": {
    "id": 1,
    "username": "new_user1",
    "email": "user1@example.com",
    "avatarUrl": "/uploads/avatars/1_demo.png"
  },
  "message": "success"
}
```

## 6. 上传头像

`POST /api/v1/user/avatar`

### 请求体

`multipart/form-data`

| 字段   | 说明     |
| ------ | -------- |
| avatar | 头像文件 |

### 成功响应

```json
{
  "code": 0,
  "data": {
    "avatarUrl": "/uploads/avatars/1_demo.png"
  },
  "message": "success"
}
```

### 失败响应

```json
{
  "code": 1000,
  "message": "请选择要上传的头像。",
  "data": null
}
```
