// localStorage key 统一管理
// 便于后续 Mock 删除时的清理

export const STORAGE_KEYS = {
  // Mock 相关数据（删除 Mock 时一起清理）
  mock: {
    evaluations: "agent-platform:mock-evaluations:v1",
  },
  // 应用数据持久化
  draft: {
    submit: "agent-platform:draft:v1",
  },
  catalog: {
    filters: "agent-platform:dataset-page:filters:v1",
  },
  user: {
    profile: "agent-platform:user:v1",
    token: "token",
    postLoginRedirect: "agent-platform:post-login-redirect",
  },
} as const;
