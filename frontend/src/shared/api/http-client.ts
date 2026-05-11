import axios from "axios";
import type { AxiosRequestConfig } from "axios";
import { ApiConfig } from "@/shared/api/Config";
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

interface ApiValidationErrorItem {
  field: string;
  reason: string;
}

interface BackendResponse<T = any> {
  code: number;
  data: T;
  message: string;
}

interface LegacyValidationErrorItem {
  msg?: string;
  loc?: Array<string | number>;
}

const axiosInstance = axios.create({
  baseURL: ApiConfig.baseUrl,
  timeout: 10000,
});

let apiLocale = "zh-CN";

export const setApiLocale = (locale: string) => {
  apiLocale = locale;
};

const buildLegacyValidationMessage = (
  errors: LegacyValidationErrorItem[],
): string => {
  if (!errors.length) return "请求参数错误";

  return errors
    .map((item) => {
      const field =
        item.loc?.filter((value) => value !== "body").join(".") || "";
      return field
        ? `${field}: ${item.msg || "参数错误"}`
        : item.msg || "参数错误";
    })
    .join("；");
};

const normalizeValidationErrors = (payload: any): ApiValidationErrorItem[] => {
  const candidateErrors = payload?.data?.errors;
  if (Array.isArray(candidateErrors)) {
    return candidateErrors
      .map((item) => {
        if (!item || typeof item !== "object") {
          return null;
        }

        const field =
          typeof item.field === "string" && item.field.trim()
            ? item.field.trim()
            : "request";
        const reason =
          typeof item.reason === "string" && item.reason.trim()
            ? item.reason.trim()
            : "参数错误";

        return { field, reason };
      })
      .filter((item): item is ApiValidationErrorItem => item !== null);
  }

  if (Array.isArray(payload?.detail)) {
    return (payload.detail as LegacyValidationErrorItem[]).map((item) => ({
      field:
        item.loc?.filter((value) => value !== "body").join(".") || "request",
      reason: item.msg || "参数错误",
    }));
  }

  return [];
};

const buildValidationMessage = (errors: ApiValidationErrorItem[]): string => {
  if (!errors.length) {
    return "请求参数错误";
  }

  return errors
    .map((item) =>
      item.field && item.field !== "request"
        ? `${item.field}: ${item.reason}`
        : item.reason,
    )
    .join("；");
};

const extractErrorMessage = (payload: any): string => {
  if (!payload) return "网络错误";

  if (typeof payload === "string") return payload;

  if (typeof payload.message === "string" && payload.message.trim()) {
    return payload.message;
  }

  const validationErrors = normalizeValidationErrors(payload);
  if (validationErrors.length > 0) {
    return buildValidationMessage(validationErrors);
  }

  if (payload.detail) {
    if (typeof payload.detail === "string") {
      return payload.detail;
    }

    if (
      typeof payload.detail.message === "string" &&
      payload.detail.message.trim()
    ) {
      return payload.detail.message;
    }

    if (Array.isArray(payload.detail)) {
      return buildLegacyValidationMessage(
        payload.detail as LegacyValidationErrorItem[],
      );
    }
  }

  return "请求失败";
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
      extractErrorMessage(responseData) || error.message || "网络错误";

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
