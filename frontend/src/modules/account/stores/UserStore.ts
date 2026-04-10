import { defineStore } from "pinia";
import { ref, computed } from "vue";
import request from "@/shared/api/core/HttpClient";
import { normalizeApiAssetUrl } from "@/shared/api/core/ApiRuntime";
import { STORAGE_KEYS } from "@/shared/constants/StorageKeys";
import { appendCacheBustParam } from "@/shared/lib/AssetDisplayUrl";

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

interface LoginResponse {
  token: string;
  user: UserPayload;
}

interface RegisterResponse {
  token: string;
  user: UserPayload;
}

interface UpdateProfileData {
  username?: string;
  password?: string;
}

const normalizeAvatarUrl = (avatarUrl?: string | null): string | null => {
  if (!avatarUrl) return null;
  return normalizeApiAssetUrl(avatarUrl);
};

const normalizeUser = (user: UserPayload): User => ({
  id: user.id,
  username: user.username,
  email: user.email,
  avatarUrl: normalizeAvatarUrl(user.avatarUrl ?? user.avatar_url ?? null),
});

export const useUserStore = defineStore("user", () => {
  const showLogin = ref(false);
  const token = ref<string | null>(
    localStorage.getItem(STORAGE_KEYS.user.token),
  );
  const currentUser = ref<User | null>(null);
  const avatarVersion = ref(Date.now());
  const postLoginRedirect = ref<string | null>(
    sessionStorage.getItem(STORAGE_KEYS.user.postLoginRedirect),
  );

  const isLogin = computed(() => Boolean(token.value && currentUser.value));
  const username = computed(() => currentUser.value?.username || "");
  const email = computed(() => currentUser.value?.email || "");
  const avatarUrl = computed(() => currentUser.value?.avatarUrl || "");
  const avatarDisplayUrl = computed(() =>
    appendCacheBustParam(avatarUrl.value, avatarVersion.value),
  );

  const clearAuthState = () => {
    localStorage.removeItem(STORAGE_KEYS.user.token);
    token.value = null;
    currentUser.value = null;
  };

  const setAuthState = (newToken: string, user: UserPayload) => {
    localStorage.setItem(STORAGE_KEYS.user.token, newToken);
    token.value = newToken;
    currentUser.value = normalizeUser(user);
  };

  const setCurrentUser = (user: UserPayload) => {
    currentUser.value = normalizeUser(user);
    avatarVersion.value = Date.now();
  };

  const restoreLogin = async (): Promise<boolean> => {
    const storedToken = localStorage.getItem(STORAGE_KEYS.user.token);
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

  const setPostLoginRedirect = (path: string | null) => {
    postLoginRedirect.value = path;

    if (path) {
      sessionStorage.setItem(STORAGE_KEYS.user.postLoginRedirect, path);
      return;
    }

    sessionStorage.removeItem(STORAGE_KEYS.user.postLoginRedirect);
  };

  const consumePostLoginRedirect = (): string | null => {
    const redirect = postLoginRedirect.value;
    setPostLoginRedirect(null);
    return redirect;
  };

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
        avatarVersion.value = Date.now();
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
    avatarDisplayUrl,
    postLoginRedirect,
    login,
    register,
    logout,
    openLoginDialog,
    setPostLoginRedirect,
    consumePostLoginRedirect,
    restoreLogin,
    fetchProfile,
    updateProfile,
    uploadAvatar,
  };
});
