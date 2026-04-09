// API 配置和环境变量的集中管理

export const DEFAULT_API_BASE_URL = "/api/v1";
export const DEFAULT_BACKEND_TARGET = "http://127.0.0.1:8001";

const normalizeEnvValue = (value?: string): string => value?.trim() ?? "";

const resolveBaseUrl = (): string =>
  normalizeEnvValue(import.meta.env.VITE_API_BASE_URL) || DEFAULT_API_BASE_URL;

const resolveBackendTarget = (): string =>
  normalizeEnvValue(import.meta.env.VITE_BACKEND_TARGET) ||
  DEFAULT_BACKEND_TARGET;

export const ApiConfig = {
  baseUrl: resolveBaseUrl(),
  backendTarget: resolveBackendTarget(),
  enableApiMock: import.meta.env.VITE_ENABLE_API_MOCK === "true",
  enableLeaderboardMock:
    import.meta.env.VITE_ENABLE_LEADERBOARD_MOCK === "true",
} as const;
