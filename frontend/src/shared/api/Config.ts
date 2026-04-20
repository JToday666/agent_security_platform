// API 配置和环境变量的集中管理

const DEFAULT_API_BASE_URL = "/api/v1";

const normalizeEnvValue = (value?: string): string => value?.trim() ?? "";

const resolveBaseUrl = (): string =>
  normalizeEnvValue(import.meta.env.VITE_API_BASE_URL) || DEFAULT_API_BASE_URL;

export const ApiConfig = {
  baseUrl: resolveBaseUrl(),
  enableApiMock: import.meta.env.VITE_ENABLE_API_MOCK === "true",
} as const;
