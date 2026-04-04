import axios from "axios";
import type { AxiosRequestConfig, AxiosResponse } from "axios";

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  code?: number;
}

export interface ApiError extends Error {
  code?: number;
  httpStatus?: number;
  data?: unknown;
}

interface BackendResponse<T = any> {
  code: number;
  data: T;
  message: string;
}

interface ValidationErrorItem {
  msg?: string;
  loc?: Array<string | number>;
}

const DEFAULT_BASE_URL = "/api/v1";

const axiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || DEFAULT_BASE_URL,
  timeout: 10000,
});

const buildValidationMessage = (errors: ValidationErrorItem[]): string => {
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

const extractErrorMessage = (payload: any): string => {
  if (!payload) return "网络错误";

  if (typeof payload === "string") return payload;

  if (typeof payload.message === "string" && payload.message.trim()) {
    return payload.message;
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
      return buildValidationMessage(payload.detail as ValidationErrorItem[]);
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
  } = {},
): ApiError => {
  const error = new Error(message) as ApiError;
  error.code = options.code;
  error.httpStatus = options.httpStatus;
  error.data = options.data;
  return error;
};

export const isApiError = (error: unknown): error is ApiError =>
  error instanceof Error && ("code" in error || "httpStatus" in error);

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

axiosInstance.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers = config.headers ?? {};
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
    const message =
      extractErrorMessage(responseData) || error.message || "网络错误";

    if (error.response?.status === 401) {
      window.dispatchEvent(
        new CustomEvent("unauthorized", {
          detail: {
            message,
            status: error.response.status,
            code: responseData?.code ?? responseData?.detail?.code,
          },
        }),
      );
    }

    return Promise.reject(
      createApiError(message, {
        code: responseData?.code ?? responseData?.detail?.code,
        httpStatus: error.response?.status,
        data: responseData?.data ?? responseData?.detail ?? responseData,
      }),
    );
  },
);

const request = {
  get: async <T = any>(
    url: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<T>> => {
    const response: AxiosResponse = await axiosInstance.get(url, config);
    return toApiResponse<T>(response.data);
  },

  post: async <T = any>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<T>> => {
    const response: AxiosResponse = await axiosInstance.post(url, data, config);
    return toApiResponse<T>(response.data);
  },

  put: async <T = any>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<T>> => {
    const response: AxiosResponse = await axiosInstance.put(url, data, config);
    return toApiResponse<T>(response.data);
  },
};

export default request;
