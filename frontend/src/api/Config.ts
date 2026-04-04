// API 配置和环境变量的集中管理

export const ApiConfig = {
  submission: {
    useLive: import.meta.env.VITE_USE_LIVE_SUBMISSION_API === "true",
  },
  reference: {
    useLive: import.meta.env.VITE_USE_LIVE_REFERENCE_API === "true",
  },
  baseUrl: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
};
