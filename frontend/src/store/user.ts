import { defineStore } from "pinia";
import { ref, computed } from "vue";

// 用户类型定义
export interface User {
	id: number;
	username: string;
	email: string;
	password: string; // 模拟用，实际不存明文
}

export const useUserStore = defineStore("user", () => {
	// 是否显示登录对话框
	const showLogin = ref(false);

	// 模拟用户数据（实际应由后端验证）
	const users = ref<User[]>([
		{
			id: 1,
			username: "admin",
			email: "admin@example.com",
			password: "123456",
		},
	]);

	// 当前登录用户（不包含密码）
	const currentUser = ref<Omit<User, "password"> | null>(null);

	// 为了兼容原有代码，保留 isLogin 和 username 的计算属性
	const isLogin = computed(() => currentUser.value !== null);
	const username = computed(() => currentUser.value?.username || "");

	// 从 localStorage 恢复登录状态
	const restoreLogin = () => {
		const savedUser = localStorage.getItem("user");
		if (savedUser) {
			try {
				currentUser.value = JSON.parse(savedUser);
			} catch (e) {
				// 解析失败则清除无效数据
				localStorage.removeItem("user");
			}
		}
	};

	// 登录动作：验证用户名和密码
	const login = (username: string, password: string): boolean => {
		const foundUser = users.value.find(
			(u) => u.username === username && u.password === password,
		);
		if (foundUser) {
			const { password: _, ...safeUser } = foundUser;
			currentUser.value = safeUser;
			// 持久化存储（不存密码）
			localStorage.setItem("user", JSON.stringify(safeUser));
			showLogin.value = false; // 登录成功关闭对话框
			return true;
		}
		return false;
	};

	// 注册动作：添加新用户
	const register = (userData: {
		username: string;
		email: string;
		password: string;
	}): boolean => {
		// 检查用户名或邮箱是否已存在
		const exists = users.value.some(
			(u) => u.username === userData.username || u.email === userData.email,
		);
		if (exists) return false;

		const newUser: User = {
			id: users.value.length + 1,
			...userData,
		};
		users.value.push(newUser);
		// 注册成功后自动登录
		const { password: _, ...safeUser } = newUser;
		currentUser.value = safeUser;
		// 持久化存储
		localStorage.setItem("user", JSON.stringify(safeUser));
		showLogin.value = false;
		return true;
	};

	// 退出登录
	const logout = () => {
		currentUser.value = null;
		localStorage.removeItem("user");
	};

	// 打开对话框（方便调用）
	const openLoginDialog = () => {
		showLogin.value = true;
	};

	return {
		// 状态
		showLogin,
		currentUser,
		// 兼容原有属性
		isLogin,
		username,
		// 方法
		login,
		register,
		logout,
		openLoginDialog,
		restoreLogin, // 导出恢复方法
	};
});
