import axios from "axios";
import type { AxiosRequestConfig, AxiosResponse } from "axios";

export interface ApiResponse<T = any> {
	success: boolean;
	data?: T;
	message?: string;
}

const axiosInstance = axios.create({
	baseURL: import.meta.env.VITE_API_BASE_URL || "/api",
	timeout: 10000,
});

axiosInstance.interceptors.request.use(
	(config) => {
		const token = localStorage.getItem("token");
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
		if (error.response?.status === 401) {
			window.dispatchEvent(new CustomEvent("unauthorized"));
		}
		const message =
			error.response?.data?.message || error.message || "网络错误";
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
			const res = response.data;
			if (res.code === 0) {
				return { success: true, data: res.data };
			} else {
				return { success: false, message: res.message || "请求失败" };
			}
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
			const res = response.data;
			if (res.code === 0) {
				return { success: true, data: res.data };
			} else {
				return { success: false, message: res.message || "请求失败" };
			}
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
			const res = response.data;
			if (res.code === 0) {
				return { success: true, data: res.data };
			} else {
				return { success: false, message: res.message || "请求失败" };
			}
		} catch (error: any) {
			throw error;
		}
	},
};

export default request;
