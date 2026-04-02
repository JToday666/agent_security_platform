# 用户信息接口文档

## 基本信息

- **基础路径**：`/api`
- **请求/响应格式**：JSON（头像上传接口除外，使用 `multipart/form-data`）
- **字符编码**：UTF-8
- **认证方式**：除登录、注册外，其他接口需在请求头中携带 `Authorization: Bearer <token>`

## 通用响应格式

### 成功响应

```json
{
  "code": 0,
  "data": { ... },   // 具体数据，可能为对象或数组
  "message": "success"
}
```

### 失败响应

```json
{
  "code": 非0整数,
  "message": "错误描述",
  "data": null
}
```

---

## 接口列表

### 1. 用户登录

- **URL**：`/auth/login`
- **方法**：`POST`
- **描述**：支持用户名或邮箱登录。

#### 请求体

```json
{
  "username": "string", // 用户名或邮箱
  "password": "string" // 密码（至少6位）
}
```

#### 成功响应（`code=0`）

```json
{
  "code": 0,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "user": {
      "id": 1,
      "username": "john_doe",
      "email": "john@example.com",
      "avatarUrl": "https://example.com/avatars/1.jpg"
    }
  },
  "message": "success"
}
```

#### 失败响应

| 错误场景          | HTTP状态码 | 响应示例                                                                  |
| ----------------- | ---------- | ------------------------------------------------------------------------- |
| 用户名/邮箱不存在 | 401        | `json { "code": 1001, "message": "用户名或密码错误", "data": null } `     |
| 密码错误          | 401        | `json { "code": 1001, "message": "用户名或密码错误", "data": null } `     |
| 请求参数缺失      | 400        | `json { "code": 1000, "message": "用户名和密码不能为空", "data": null } ` |
| 密码长度不足6位   | 400        | `json { "code": 1000, "message": "密码长度至少6位", "data": null } `      |

---

### 2. 用户注册

- **URL**：`/auth/register`
- **方法**：`POST`
- **描述**：新用户注册，注册成功后自动登录，返回 token 和用户信息。

#### 请求体

```json
{
  "username": "string", // 用户名（唯一）
  "email": "string", // 邮箱（唯一）
  "password": "string" // 密码（至少6位）
}
```

#### 成功响应（`code=0`）

```json
{
  "code": 0,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "user": {
      "id": 2,
      "username": "jane_doe",
      "email": "jane@example.com",
      "avatarUrl": null // 初始头像可为空
    }
  },
  "message": "success"
}
```

#### 失败响应

| 错误场景        | HTTP状态码 | 响应示例                                                                        |
| --------------- | ---------- | ------------------------------------------------------------------------------- |
| 用户名已被占用  | 409        | `json { "code": 1002, "message": "用户名已被注册", "data": null } `             |
| 邮箱已被占用    | 409        | `json { "code": 1002, "message": "邮箱已被注册", "data": null } `               |
| 密码长度不足6位 | 400        | `json { "code": 1000, "message": "密码长度至少6位", "data": null } `            |
| 邮箱格式不正确  | 400        | `json { "code": 1000, "message": "邮箱格式不正确", "data": null } `             |
| 用户名/邮箱为空 | 400        | `json { "code": 1000, "message": "用户名、邮箱和密码不能为空", "data": null } ` |

---

### 3. 获取当前用户信息

- **URL**：`/auth/me`
- **方法**：`GET`
- **描述**：通过 token 获取当前登录用户的详细信息。

#### 请求头

```
Authorization: Bearer <token>
```

#### 成功响应（`code=0`）

```json
{
  "code": 0,
  "data": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "avatarUrl": "https://example.com/avatars/1.jpg"
  },
  "message": "success"
}
```

#### 失败响应

| 错误场景        | HTTP状态码 | 响应示例                                                               |
| --------------- | ---------- | ---------------------------------------------------------------------- |
| 未提供 token    | 401        | `json { "code": 401, "message": "未授权，请先登录", "data": null } `   |
| token 无效/过期 | 401        | `json { "code": 401, "message": "token 无效或已过期", "data": null } ` |

---

### 4. 获取用户详细信息（个人资料页）

- **URL**：`/user/profile`
- **方法**：`GET`
- **描述**：同 `/auth/me`，用于个人资料页初始化。

#### 请求头

```
Authorization: Bearer <token>
```

#### 成功响应（`code=0`）

```json
{
  "code": 0,
  "data": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "avatarUrl": "https://example.com/avatars/1.jpg"
  },
  "message": "success"
}
```

#### 失败响应

同 `/auth/me`。

---

### 5. 更新个人信息（用户名/密码）

- **URL**：`/user/profile`
- **方法**：`PUT`
- **描述**：允许用户修改用户名和密码。**邮箱不可修改**。修改用户名时需要检查唯一性。

#### 请求头

```
Authorization: Bearer <token>
```

#### 请求体

```json
{
  "username": "new_username", // 可选，新用户名（唯一）
  "password": "new_password" // 可选，新密码（至少6位）
}
```

#### 成功响应（`code=0`）

返回更新后的用户信息：

```json
{
  "code": 0,
  "data": {
    "id": 1,
    "username": "new_username",
    "email": "john@example.com",
    "avatarUrl": "https://example.com/avatars/1.jpg"
  },
  "message": "success"
}
```

#### 失败响应

| 错误场景               | HTTP状态码 | 响应示例                                                                  |
| ---------------------- | ---------- | ------------------------------------------------------------------------- |
| 用户名已被占用         | 409        | `json { "code": 1003, "message": "用户名已被占用", "data": null } `       |
| 新密码长度不足6位      | 400        | `json { "code": 1000, "message": "密码长度至少6位", "data": null } `      |
| 未提供任何可修改字段   | 400        | `json { "code": 1000, "message": "没有提供要修改的字段", "data": null } ` |
| 尝试修改邮箱（不允许） | 403        | `json { "code": 1004, "message": "邮箱不可修改", "data": null } `         |
| token 无效/过期        | 401        | 同接口3失败响应                                                           |

---

### 6. 上传头像

- **URL**：`/user/avatar`
- **方法**：`POST`
- **描述**：上传用户头像，支持常见图片格式，大小不超过 2MB。

#### 请求头

```
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

#### 请求体（FormData）

| 字段名 | 类型 | 说明                                |
| ------ | ---- | ----------------------------------- |
| avatar | File | 图片文件，支持 JPG、PNG，大小 ≤ 2MB |

#### 成功响应（`code=0`）

```json
{
  "code": 0,
  "data": {
    "avatarUrl": "https://example.com/avatars/1_new.jpg"
  },
  "message": "success"
}
```

#### 失败响应

| 错误场景               | HTTP状态码 | 响应示例                                                                     |
| ---------------------- | ---------- | ---------------------------------------------------------------------------- |
| 未上传文件             | 400        | `json { "code": 1000, "message": "请选择要上传的头像", "data": null } `      |
| 文件大小超过 2MB       | 400        | `json { "code": 1000, "message": "头像大小不能超过 2MB", "data": null } `    |
| 文件类型不支持         | 400        | `json { "code": 1000, "message": "仅支持 JPG、PNG 格式", "data": null } `    |
| 上传失败（服务器错误） | 500        | `json { "code": 500, "message": "头像上传失败，请稍后重试", "data": null } ` |
| token 无效/过期        | 401        | 同接口3失败响应                                                              |

---

## 附录：错误码说明

| 错误码 | 含义                               |
| ------ | ---------------------------------- |
| 0      | 成功                               |
| 1000   | 请求参数错误（通用）               |
| 1001   | 登录失败（用户名/邮箱或密码错误）  |
| 1002   | 注册失败（用户名或邮箱已被注册）   |
| 1003   | 更新个人信息失败（用户名已被占用） |
| 1004   | 更新个人信息失败（邮箱不可修改）   |
| 401    | 未授权或 token 无效                |
| 500    | 服务器内部错误                     |
