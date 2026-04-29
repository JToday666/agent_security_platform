# 用户及认证接口协议

## 1. 用户登录

`POST /api/v1/auth/login`

- **作用**：验证凭据发还 Token。
- **请求体**：

```json
{
  "username": "user1",
  "password": "password123"
}
```

- **响应**：

```json
{
  "code": 0,
  "data": {
    "token": "eyJhbGci...",
    "expiresIn": 86400
  },
  "message": "success"
}
```

## 2. 获取当前用户信息

`GET /api/v1/auth/profile`

- **作用**：带上 Token 获取登录者信息。
- **响应**：

```json
{
  "code": 0,
  "data": {
    "userId": "usr_x",
    "username": "user1",
    "avatar": "https://..."
  },
  "message": "success"
}
```

_备注：前端仅维护在内存状态，错误或 401 时跳转登录，不使用 LocalStorage 存储用户信息。_
