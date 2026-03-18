import { defineStore } from "pinia";
import { ref, computed } from "vue";
import request from "@/utils/request";

// 用户类型定义
export interface User {
  id: number;
  username: string;
  email: string;
  avatarUrl: string | null;
}

interface UserPayload {
  id: number;
  username: string;
  email: string;
  avatarUrl?: string | null;
  avatar_url?: string | null;
}

// 登录响应数据类型
interface LoginResponse {
  token: string;
  user: UserPayload;
}

// 注册响应数据类型
interface RegisterResponse {
  token: string;
  user: UserPayload;
}

// 更新个人信息请求体
interface UpdateProfileData {
  username?: string;
  password?: string;
}

const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL || "/api/v1";

const resolveApiOrigin = (): string | null => {
  if (!/^https?:\/\//i.test(API_BASE_URL)) return null;

  try {
    return new URL(API_BASE_URL).origin;
  } catch {
    return null;
  }
};

const API_ORIGIN = resolveApiOrigin();

const normalizeAvatarUrl = (avatarUrl?: string | null): string | null => {
  if (!avatarUrl) return null;

  if (/^https?:\/\//i.test(avatarUrl)) {
    return avatarUrl;
  }

  if (!API_ORIGIN) {
    return avatarUrl;
  }

  if (avatarUrl.startsWith("/")) {
    return `${API_ORIGIN}${avatarUrl}`;
  }

  return `${API_ORIGIN}/${avatarUrl}`;
};

const normalizeUser = (user: UserPayload): User => ({
  id: user.id,
  username: user.username,
  email: user.email,
  avatarUrl: normalizeAvatarUrl(user.avatarUrl ?? user.avatar_url ?? null),
});

export const useUserStore = defineStore("user", () => {
  const showLogin = ref(false);
  const token = ref<string | null>(localStorage.getItem("token"));
  const currentUser = ref<User | null>(null);

  const isLogin = computed(() => Boolean(token.value && currentUser.value));
  const username = computed(() => currentUser.value?.username || "");
  const email = computed(() => currentUser.value?.email || "");
  const avatarUrl = computed(() => currentUser.value?.avatarUrl || "");

  const clearAuthState = () => {
    localStorage.removeItem("token");
    token.value = null;
    currentUser.value = null;
  };

  const setAuthState = (newToken: string, user: UserPayload) => {
    localStorage.setItem("token", newToken);
    token.value = newToken;
    currentUser.value = normalizeUser(user);
  };

  const setCurrentUser = (user: UserPayload) => {
    currentUser.value = normalizeUser(user);
  };

  /* 从 localStorage 恢复登录状态 */
  const restoreLogin = async (): Promise<boolean> => {
    const storedToken = localStorage.getItem("token");
    if (!storedToken) return false;

    token.value = storedToken;

    try {
      const res = await request.get<UserPayload>("/auth/me");
      if (res.success && res.data) {
        setCurrentUser(res.data);
        return true;
      }

      clearAuthState();
      return false;
    } catch {
      clearAuthState();
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
        setAuthState(res.data.token, res.data.user);
        showLogin.value = false;
        return true;
      }

      throw new Error(res.message || "登录失败");
    } catch (error: any) {
      const message = error.message || "用户名/邮箱或密码错误";
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
        setAuthState(res.data.token, res.data.user);
        showLogin.value = false;
        return true;
      }

      throw new Error(res.message || "注册失败");
    } catch (error: any) {
      const message = error.message || "用户名或邮箱已被注册";
      throw new Error(message);
    }
  };

  const logout = () => {
    clearAuthState();
  };

  const openLoginDialog = () => {
    showLogin.value = true;
  };

  /* 获取当前用户详细信息 */
  const fetchProfile = async (): Promise<boolean> => {
    try {
      const res = await request.get<UserPayload>("/user/profile");
      if (res.success && res.data) {
        setCurrentUser(res.data);
        return true;
      }
      return false;
    } catch {
      return false;
    }
  };

  /* 更新个人信息（用户名、密码） */
  const updateProfile = async (data: UpdateProfileData): Promise<boolean> => {
    try {
      const res = await request.put<UserPayload>("/user/profile", data);
      if (res.success && res.data) {
        setCurrentUser(res.data);
        return true;
      }

      throw new Error(res.message || "更新失败");
    } catch (error: any) {
      const message = error.message || "更新失败";
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
        const newAvatarUrl = normalizeAvatarUrl(res.data.avatarUrl);
        if (currentUser.value) {
          currentUser.value.avatarUrl = newAvatarUrl;
        }
        return newAvatarUrl || "";
      }

      throw new Error(res.message || "头像上传失败");
    } catch (error: any) {
      const message = error.message || "头像上传失败";
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
