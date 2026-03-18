import axios, { AxiosHeaders } from "axios";
import type { AxiosRequestConfig, AxiosResponse } from "axios";

export interface BackendEnvelope<T = unknown> {
  code: number;
  data: T | null;
  message: string;
}

export interface ApiError {
  status: number;
  code?: number;
  message: string;
  raw?: unknown;
}

const DEFAULT_ERROR_MESSAGE = "网络错误";
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api/v1";

const axiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
});

const isApiError = (error: unknown): error is ApiError => {
  if (!error || typeof error !== "object") {
    return false;
  }
  return "status" in error && "message" in error;
};

const extractValidationMessage = (detail: unknown): string | null => {
  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }
  if (Array.isArray(detail) && detail.length > 0) {
    const firstError = detail[0];
    if (firstError && typeof firstError === "object") {
      const msg = (firstError as Record<string, unknown>).msg;
      if (typeof msg === "string" && msg.trim()) {
        return msg;
      }
    }
  }
  return null;
};

const normalizeApiError = (error: unknown): ApiError => {
  if (isApiError(error)) {
    return error;
  }

  const axiosError = error as any;
  const status = Number(axiosError?.response?.status ?? 0);
  const responseData = axiosError?.response?.data;
  const responseCode =
    typeof responseData?.code === "number" ? responseData.code : undefined;

  let message =
    typeof responseData?.message === "string" && responseData.message.trim() ?
      responseData.message
    : axiosError?.message || DEFAULT_ERROR_MESSAGE;

  if (status === 422 && !responseData?.message) {
    const validationMessage = extractValidationMessage(responseData?.detail);
    if (validationMessage) {
      message = validationMessage;
    }
  }

  return {
    status,
    code: responseCode,
    message,
    raw: responseData ?? error,
  };
};

export const toApiError = (error: unknown): ApiError =>
  normalizeApiError(error);

const isPublicAuthEndpoint = (url?: string): boolean => {
  if (!url) {
    return false;
  }
  return url.includes("/auth/login") || url.includes("/auth/register");
};

axiosInstance.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token");
    if (token) {
      const headers = AxiosHeaders.from(config.headers || {});
      headers.set("Authorization", `Bearer ${token}`);
      config.headers = headers;
    }
    return config;
  },
  (error) => Promise.reject(normalizeApiError(error)),
);

axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    const normalized = normalizeApiError(error);
    const status = Number(error?.response?.status ?? 0);
    const requestUrl = error?.config?.url as string | undefined;
    if (status === 401 && !isPublicAuthEndpoint(requestUrl)) {
      window.dispatchEvent(new CustomEvent("unauthorized"));
    }
    return Promise.reject(normalized);
  },
);

const unwrapEnvelope = <T>(response: AxiosResponse<BackendEnvelope<T>>): T => {
  const payload = response.data;
  if (!payload || typeof payload.code !== "number") {
    throw {
      status: response.status,
      message: "响应格式不正确",
      raw: payload,
    } satisfies ApiError;
  }
  if (payload.code !== 0) {
    throw {
      status: response.status,
      code: payload.code,
      message: payload.message || "请求失败",
      raw: payload,
    } satisfies ApiError;
  }
  return payload.data as T;
};

const request = {
  get: async <T = unknown>(
    url: string,
    config?: AxiosRequestConfig,
  ): Promise<T> => {
    try {
      const response = await axiosInstance.get<BackendEnvelope<T>>(url, config);
      return unwrapEnvelope<T>(response);
    } catch (error) {
      throw normalizeApiError(error);
    }
  },

  post: async <T = unknown>(
    url: string,
    data?: unknown,
    config?: AxiosRequestConfig,
  ): Promise<T> => {
    try {
      const response = await axiosInstance.post<BackendEnvelope<T>>(
        url,
        data,
        config,
      );
      return unwrapEnvelope<T>(response);
    } catch (error) {
      throw normalizeApiError(error);
    }
  },

  put: async <T = unknown>(
    url: string,
    data?: unknown,
    config?: AxiosRequestConfig,
  ): Promise<T> => {
    try {
      const response = await axiosInstance.put<BackendEnvelope<T>>(
        url,
        data,
        config,
      );
      return unwrapEnvelope<T>(response);
    } catch (error) {
      throw normalizeApiError(error);
    }
  },
};

export default request;
