import { defineStore } from "pinia";
import { ref, computed } from "vue";
// import type { ApiResponse } from "@/utils/request";
import request from "@/utils/request";

// 用户类型定义
export interface User {
	id: number;
	username: string;
	email: string;
	avatarUrl?: string;
}

// 登录响应数据类型
interface LoginResponse {
	token: string;
	user: User;
}

// 注册响应数据类型
interface RegisterResponse {
	token: string;
	user: User;
}

// 更新个人信息请求体
interface UpdateProfileData {
	username?: string;
	email?: string;
	password?: string;
}

export const useUserStore = defineStore("user", () => {
	const showLogin = ref(false);
	const token = ref<string | null>(localStorage.getItem("token"));
	const currentUser = ref<User | null>(null);

	const isLogin = computed(() => currentUser.value !== null);
	const username = computed(() => currentUser.value?.username || "");
	const email = computed(() => currentUser.value?.email || "");
	const avatarUrl = computed(() => currentUser.value?.avatarUrl || "");

	/* 从 localStorage 恢复登录状态 */
	const restoreLogin = async (): Promise<boolean> => {
		const storedToken = localStorage.getItem("token");
		if (!storedToken) return false;

		try {
			const res = await request.get<User>("/auth/me");
			if (res.success && res.data) {
				currentUser.value = res.data;
				token.value = storedToken;
				return true;
			} else {
				localStorage.removeItem("token");
				token.value = null;
				return false;
			}
		} catch (error) {
			localStorage.removeItem("token");
			token.value = null;
			return false;
		}
	};

	const login = async (
		identifier: string,
		password: string,
	): Promise<boolean> => {
		try {
			const res = await request.post<LoginResponse>("/auth/login", {
				username: identifier,
				password,
			});

			if (res.success && res.data) {
				const { token: newToken, user } = res.data;
				localStorage.setItem("token", newToken);
				token.value = newToken;
				currentUser.value = user;
				showLogin.value = false;
				return true;
			} else {
				throw new Error(res.message || "登录失败");
			}
		} catch (error: any) {
			const message =
				error.response?.data?.message ||
				error.message ||
				"用户名/邮箱或密码错误";
			throw new Error(message);
		}
	};

	const register = async (userData: {
		username: string;
		email: string;
		password: string;
	}): Promise<boolean> => {
		try {
			const res = await request.post<RegisterResponse>(
				"/auth/register",
				userData,
			);

			if (res.success && res.data) {
				const { token: newToken, user } = res.data;
				localStorage.setItem("token", newToken);
				token.value = newToken;
				currentUser.value = user;
				showLogin.value = false;
				return true;
			} else {
				throw new Error(res.message || "注册失败");
			}
		} catch (error: any) {
			const message =
				error.response?.data?.message ||
				error.message ||
				"用户名或邮箱已被注册";
			throw new Error(message);
		}
	};

	const logout = () => {
		localStorage.removeItem("token");
		token.value = null;
		currentUser.value = null;
	};

	const openLoginDialog = () => {
		showLogin.value = true;
	};

	/* 获取当前用户详细信息 */
	const fetchProfile = async (): Promise<boolean> => {
		try {
			const res = await request.get<User>("/user/profile");
			if (res.success && res.data) {
				currentUser.value = {
					...currentUser.value,
					...res.data,
				};
				return true;
			}
			return false;
		} catch (error) {
			return false;
		}
	};

	/* 更新个人信息（用户名、邮箱、密码） */
	const updateProfile = async (data: UpdateProfileData): Promise<boolean> => {
		try {
			const res = await request.put<User>("/user/profile", data);
			if (res.success && res.data) {
				currentUser.value = {
					...currentUser.value,
					...res.data,
				};
				return true;
			} else {
				throw new Error(res.message || "更新失败");
			}
		} catch (error: any) {
			const message =
				error.response?.data?.message || error.message || "更新失败";
			throw new Error(message);
		}
	};

	/* 上传头像 */
	const uploadAvatar = async (file: File): Promise<string> => {
		const formData = new FormData();
		formData.append("avatar", file);

		try {
			const res = await request.post<{ avatarUrl: string }>(
				"/user/avatar",
				formData,
			);
			if (res.success && res.data) {
				const newAvatarUrl = res.data.avatarUrl;
				if (currentUser.value) {
					currentUser.value.avatarUrl = newAvatarUrl;
				}
				return newAvatarUrl;
			} else {
				throw new Error(res.message || "头像上传失败");
			}
		} catch (error: any) {
			const message =
				error.response?.data?.message || error.message || "头像上传失败";
			throw new Error(message);
		}
	};

	return {
		showLogin,
		currentUser,
		token,
		isLogin,
		username,
		email,
		avatarUrl,
		login,
		register,
		logout,
		openLoginDialog,
		restoreLogin,
		fetchProfile,
		updateProfile,
		uploadAvatar,
	};
});
