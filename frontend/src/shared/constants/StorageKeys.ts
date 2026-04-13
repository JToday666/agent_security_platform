// localStorage key 统一管理
// 便于后续 Mock 删除时的清理

export const STORAGE_KEYS = {
  // Mock 相关数据（删除 Mock 时一起清理）
  mock: {
    evaluations: "agent-platform:mock-evaluations:v1",
  },
  // 应用数据持久化
  session: {
    scroll: "agent-platform:session-scroll:v1",
  },
  user: {
    token: "token",
    postLoginRedirect: "agent-platform:post-login-redirect",
  },
} as const;
