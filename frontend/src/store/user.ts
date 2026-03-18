import { defineStore } from "pinia";
import { ref, computed } from "vue";
import request, { toApiError } from "@/utils/request";

// 用户类型定义
export interface User {
  id: number;
  username: string;
  email: string;
  avatarUrl: string | null;
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
  password?: string;
}

const TOKEN_KEY = "token";
const USERNAME_MIN_LENGTH = 3;
const USERNAME_MAX_LENGTH = 50;
const PASSWORD_MIN_LENGTH = 6;
const PASSWORD_MAX_LENGTH = 128;
const AVATAR_MAX_SIZE = 2 * 1024 * 1024;
const AVATAR_ALLOWED_TYPES = new Set(["image/jpeg", "image/png"]);

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const normalizeUser = (user: User): User => ({
  ...user,
  avatarUrl: user.avatarUrl ?? null,
});

const getErrorMessage = (error: unknown, fallback: string): string => {
  const normalized = toApiError(error);
  return normalized.message || fallback;
};

const isUnauthorizedError = (error: unknown): boolean => {
  const normalized = toApiError(error);
  return (
    normalized.status === 401 ||
    normalized.status === 403 ||
    normalized.code === 401
  );
};

export const useUserStore = defineStore("user", () => {
  const showLogin = ref(false);
  const token = ref<string | null>(localStorage.getItem(TOKEN_KEY));
  const currentUser = ref<User | null>(null);
  const authReady = ref(false);
  const authInitPromise = ref<Promise<boolean> | null>(null);
  const redirectAfterLogin = ref<string | null>(null);

  const isLogin = computed(() => currentUser.value !== null);
  const username = computed(() => currentUser.value?.username || "");
  const email = computed(() => currentUser.value?.email || "");
  const avatarUrl = computed(() => currentUser.value?.avatarUrl ?? null);

  const setToken = (value: string | null) => {
    if (value) {
      localStorage.setItem(TOKEN_KEY, value);
    } else {
      localStorage.removeItem(TOKEN_KEY);
    }
    token.value = value;
  };

  const clearAuthState = () => {
    setToken(null);
    currentUser.value = null;
  };

  const setRedirectAfterLogin = (path: string | null) => {
    if (path && path.startsWith("/")) {
      redirectAfterLogin.value = path;
      return;
    }
    redirectAfterLogin.value = null;
  };

  const consumeRedirectAfterLogin = (): string | null => {
    const redirect = redirectAfterLogin.value;
    redirectAfterLogin.value = null;
    return redirect;
  };

  const openLoginDialog = (redirectPath?: string) => {
    setRedirectAfterLogin(redirectPath ?? null);
    showLogin.value = true;
  };

  const initAuth = async (): Promise<boolean> => {
    if (authReady.value) {
      return isLogin.value;
    }
    if (authInitPromise.value) {
      return authInitPromise.value;
    }

    authInitPromise.value = (async () => {
      const storedToken = localStorage.getItem(TOKEN_KEY);
      if (!storedToken) {
        clearAuthState();
        authReady.value = true;
        return false;
      }

      token.value = storedToken;

      try {
        const profile = await request.get<User>("/auth/me");
        currentUser.value = normalizeUser(profile);
        authReady.value = true;
        return true;
      } catch (error) {
        if (isUnauthorizedError(error)) {
          clearAuthState();
          showLogin.value = true;
        } else {
          currentUser.value = null;
        }
        authReady.value = true;
        return false;
      } finally {
        authInitPromise.value = null;
      }
    })();

    return authInitPromise.value as Promise<boolean>;
  };

  /* 从 localStorage 恢复登录状态 */
  const restoreLogin = async (): Promise<boolean> => {
    return initAuth();
  };

  const login = async (
    identifier: string,
    password: string,
  ): Promise<boolean> => {
    try {
      const usernameValue = identifier.trim();
      if (!usernameValue) {
        throw new Error("用户名或邮箱不能为空");
      }
      if (
        password.length < PASSWORD_MIN_LENGTH ||
        password.length > PASSWORD_MAX_LENGTH
      ) {
        throw new Error("密码长度需在 6-128 位之间");
      }

      const res = await request.post<LoginResponse>("/auth/login", {
        username: usernameValue,
        password,
      });

      setToken(res.token);
      currentUser.value = normalizeUser(res.user);
      showLogin.value = false;
      authReady.value = true;
      return true;
    } catch (error) {
      const message = getErrorMessage(error, "用户名/邮箱或密码错误");
      throw new Error(message);
    }
  };

  const register = async (userData: {
    username: string;
    email: string;
    password: string;
  }): Promise<boolean> => {
    try {
      const usernameValue = userData.username.trim();
      const emailValue = userData.email.trim();
      const passwordValue = userData.password;

      if (
        usernameValue.length < USERNAME_MIN_LENGTH ||
        usernameValue.length > USERNAME_MAX_LENGTH
      ) {
        throw new Error("用户名长度需在 3-50 位之间");
      }
      if (!EMAIL_REGEX.test(emailValue)) {
        throw new Error("邮箱格式不正确");
      }
      if (
        passwordValue.length < PASSWORD_MIN_LENGTH ||
        passwordValue.length > PASSWORD_MAX_LENGTH
      ) {
        throw new Error("密码长度需在 6-128 位之间");
      }

      const res = await request.post<RegisterResponse>("/auth/register", {
        username: usernameValue,
        email: emailValue,
        password: passwordValue,
      });

      setToken(res.token);
      currentUser.value = normalizeUser(res.user);
      showLogin.value = false;
      authReady.value = true;
      return true;
    } catch (error) {
      const message = getErrorMessage(error, "用户名或邮箱已被注册");
      throw new Error(message);
    }
  };

  const logout = () => {
    clearAuthState();
    showLogin.value = false;
    redirectAfterLogin.value = null;
    authReady.value = true;
  };

  const handleUnauthorized = () => {
    const hasToken = Boolean(token.value || localStorage.getItem(TOKEN_KEY));
    clearAuthState();
    authReady.value = true;
    if (hasToken) {
      showLogin.value = true;
    }
  };

  /* 获取当前用户详细信息 */
  const fetchProfile = async (): Promise<boolean> => {
    try {
      const profile = await request.get<User>("/user/profile");
      currentUser.value = normalizeUser(profile);
      return true;
    } catch {
      return false;
    }
  };

  /* 更新个人信息（用户名、密码） */
  const updateProfile = async (data: UpdateProfileData): Promise<boolean> => {
    try {
      const payload: UpdateProfileData = {};

      if (typeof data.username === "string") {
        const usernameValue = data.username.trim();
        if (!usernameValue) {
          throw new Error("用户名不能为空");
        }
        if (
          usernameValue.length < USERNAME_MIN_LENGTH ||
          usernameValue.length > USERNAME_MAX_LENGTH
        ) {
          throw new Error("用户名长度需在 3-50 位之间");
        }
        payload.username = usernameValue;
      }

      if (typeof data.password === "string" && data.password.length > 0) {
        if (
          data.password.length < PASSWORD_MIN_LENGTH ||
          data.password.length > PASSWORD_MAX_LENGTH
        ) {
          throw new Error("密码长度需在 6-128 位之间");
        }
        payload.password = data.password;
      }

      if (!payload.username && !payload.password) {
        throw new Error("没有提供要修改的字段");
      }

      const profile = await request.put<User>("/user/profile", payload);
      currentUser.value = normalizeUser(profile);
      return true;
    } catch (error) {
      const message = getErrorMessage(error, "更新失败");
      throw new Error(message);
    }
  };

  /* 上传头像 */
  const uploadAvatar = async (file: File): Promise<string> => {
    if (!AVATAR_ALLOWED_TYPES.has(file.type)) {
      throw new Error("仅支持 JPG、PNG 格式");
    }
    if (file.size > AVATAR_MAX_SIZE) {
      throw new Error("头像大小不能超过 2MB");
    }

    const formData = new FormData();
    formData.append("avatar", file);

    try {
      const res = await request.post<{ avatarUrl: string }>(
        "/user/avatar",
        formData,
      );
      const newAvatarUrl = res.avatarUrl;
      if (currentUser.value) {
        currentUser.value.avatarUrl = newAvatarUrl;
      }
      return newAvatarUrl;
    } catch (error) {
      const message = getErrorMessage(error, "头像上传失败");
      throw new Error(message);
    }
  };

  return {
    showLogin,
    currentUser,
    token,
    isLogin,
    authReady,
    authInitPromise,
    redirectAfterLogin,
    username,
    email,
    avatarUrl,
    initAuth,
    login,
    register,
    logout,
    handleUnauthorized,
    openLoginDialog,
    setRedirectAfterLogin,
    consumeRedirectAfterLogin,
    restoreLogin,
    fetchProfile,
    updateProfile,
    uploadAvatar,
  };
});
