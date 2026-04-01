import axios from "axios";
import type { AxiosRequestConfig, AxiosResponse } from "axios";

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  code?: number;
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

// 把后端校验错误拼成可直接展示的中文提示。
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
    const message =
      extractErrorMessage(error.response?.data) || error.message || "网络错误";

    if (error.response?.status === 401) {
      // 统一抛出未授权事件，由应用入口处理登录弹窗和路由回退。
      window.dispatchEvent(
        new CustomEvent("unauthorized", {
          detail: {
            message,
            status: error.response.status,
            code:
              error.response.data?.code ?? error.response.data?.detail?.code,
          },
        }),
      );
    }

    return Promise.reject(new Error(message));
  },
);

const request = {
  get: async <T = any>(
    url: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<T>> => {
    try {
      const response: AxiosResponse = await axiosInstance.get(url, config);
      return toApiResponse<T>(response.data);
    } catch (error: any) {
      throw error;
    }
  },

  post: async <T = any>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<T>> => {
    try {
      const response: AxiosResponse = await axiosInstance.post(
        url,
        data,
        config,
      );
      return toApiResponse<T>(response.data);
    } catch (error: any) {
      throw error;
    }
  },

  put: async <T = any>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<T>> => {
    try {
      const response: AxiosResponse = await axiosInstance.put(
        url,
        data,
        config,
      );
      return toApiResponse<T>(response.data);
    } catch (error: any) {
      throw error;
    }
  },
};

export default request;
