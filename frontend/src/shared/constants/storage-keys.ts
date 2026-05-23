// localStorage key 统一管理

export const STORAGE_KEYS = {
  // 应用数据持久化
  session: {
    scroll: "agent-platform:session-scroll:v1",
  },
  i18n: {
    displayLocale: "agent-platform:i18n:display-locale",
  },
  user: {
    token: "token",
    postLoginRedirect: "agent-platform:post-login-redirect",
  },
} as const;
