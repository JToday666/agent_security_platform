import axios from "axios";
import type { AxiosRequestConfig } from "axios";
import { ApiConfig } from "@/shared/api/config";
import {
  extractErrorMessage,
  normalizeValidationErrors,
  type ApiValidationErrorItem,
} from "@/shared/api/api-error-normalizer";
import { STORAGE_KEYS } from "@/shared/constants/storage-keys";

export interface ApiRequestConfig extends AxiosRequestConfig {
  skipUnauthorizedEvent?: boolean;
}

interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  code?: number;
}

export interface ApiBlobResponse {
  blob: Blob;
  fileName: string;
}

interface ApiError extends Error {
  code?: number;
  httpStatus?: number;
  data?: unknown;
  validationErrors?: ApiValidationErrorItem[];
}

interface BackendResponse<T = any> {
  code: number;
  data: T;
  message: string;
}

const axiosInstance = axios.create({
  baseURL: ApiConfig.baseUrl,
  timeout: 10000,
});

let apiLocale = "zh-CN";

export const setApiLocale = (locale: string) => {
  apiLocale = locale;
};

const createApiError = (
  message: string,
  options: {
    code?: number;
    httpStatus?: number;
    data?: unknown;
    validationErrors?: ApiValidationErrorItem[];
  } = {},
): ApiError => {
  const error = new Error(message) as ApiError;
  error.code = options.code;
  error.httpStatus = options.httpStatus;
  error.data = options.data;
  error.validationErrors = options.validationErrors;
  return error;
};

const toApiResponse = <T = any>(payload: any): ApiResponse<T> => {
  const response = payload as BackendResponse<T>;
  if (response?.code === 0) {
    return { success: true, data: response.data, code: response.code };
  }

  return {
    success: false,
    code: response?.code,
    message: extractErrorMessage(response),
  };
};

const resolveResponse = async <T = any>(
  requestPromise: Promise<{ data: unknown }>,
): Promise<ApiResponse<T>> => toApiResponse<T>((await requestPromise).data);

const readHeaderValue = (headers: unknown, name: string): string | undefined => {
  if (!headers || typeof headers !== "object") {
    return undefined;
  }

  const getter = (headers as { get?: (headerName: string) => unknown }).get;
  if (typeof getter === "function") {
    const value = getter.call(headers, name);
    if (typeof value === "string") {
      return value;
    }
  }

  const record = headers as Record<string, unknown>;
  const value = record[name] ?? record[name.toLowerCase()];
  return typeof value === "string" ? value : undefined;
};

const parseFileName = (value?: string): string => {
  if (!value) {
    return "";
  }

  const utf8Match = /filename\*=UTF-8''([^;]+)/i.exec(value);
  if (utf8Match?.[1]) {
    return decodeURIComponent(utf8Match[1].replace(/"/g, ""));
  }

  const fallbackMatch = /filename="?([^"]+)"?/i.exec(value);
  return fallbackMatch?.[1]?.trim() ?? "";
};

const resolveBlobResponse = async (
  requestPromise: Promise<{ data: unknown; headers?: Record<string, string> }>,
): Promise<ApiBlobResponse> => {
  const response = await requestPromise;
  return {
    blob: response.data as Blob,
    fileName: parseFileName(response.headers?.["content-disposition"]),
  };
};

axiosInstance.interceptors.request.use(
  (config) => {
    config.headers = config.headers ?? {};
    config.headers["X-App-Locale"] = apiLocale;
    config.headers["Accept-Language"] = apiLocale;

    const token = localStorage.getItem(STORAGE_KEYS.user.token);
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error),
);

axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    const responseData = error.response?.data;
    const validationErrors = normalizeValidationErrors(responseData);
    const message =
      extractErrorMessage(responseData, {
        httpStatus: error.response?.status,
        contentType: readHeaderValue(error.response?.headers, "content-type"),
      }) ||
      error.message ||
      extractErrorMessage(null);

    const requestConfig = error.config as ApiRequestConfig | undefined;
    const shouldDispatchUnauthorizedEvent =
      error.response?.status === 401 && !requestConfig?.skipUnauthorizedEvent;

    if (shouldDispatchUnauthorizedEvent) {
      window.dispatchEvent(
        new CustomEvent("unauthorized", {
          detail: {
            message,
            status: error.response.status,
            code: responseData?.code,
          },
        }),
      );
    }

    return Promise.reject(
      createApiError(message, {
        code: responseData?.code,
        httpStatus: error.response?.status,
        data: responseData?.data ?? responseData,
        validationErrors,
      }),
    );
  },
);

const request = {
  get: <T = any>(
    url: string,
    config?: ApiRequestConfig,
  ): Promise<ApiResponse<T>> =>
    resolveResponse<T>(axiosInstance.get(url, config)),

  post: <T = any>(
    url: string,
    data?: any,
    config?: ApiRequestConfig,
  ): Promise<ApiResponse<T>> =>
    resolveResponse<T>(axiosInstance.post(url, data, config)),

  put: <T = any>(
    url: string,
    data?: any,
    config?: ApiRequestConfig,
  ): Promise<ApiResponse<T>> =>
    resolveResponse<T>(axiosInstance.put(url, data, config)),

  download: (
    url: string,
    config?: ApiRequestConfig,
  ): Promise<ApiBlobResponse> =>
    resolveBlobResponse(
      axiosInstance.get(url, { ...config, responseType: "blob" }),
    ),
};

export default request;
