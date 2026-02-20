<template>
  <Teleport to="body">
    <div v-if="showLogin" class="dialog-overlay" @click.self="closeDialog">
      <div class="dialog-card">
        <!-- 关闭按钮 -->
        <button class="close-btn" @click="closeDialog">✕</button>

        <!-- 标题与模式切换 -->
        <h3>{{ mode === "login" ? "登录" : "注册" }}</h3>

        <!-- 登录表单 -->
        <form v-if="mode === 'login'" @submit.prevent="handleLogin">
          <div class="form-group">
            <input v-model="loginForm.username" type="text" placeholder="用户名" required />
          </div>
          <div class="form-group">
            <input v-model="loginForm.password" type="password" placeholder="密码" required />
          </div>
          <div v-if="loginError" class="error-message">{{ loginError }}</div>
          <button type="submit" class="submit-btn" :disabled="!isLoginValid">登录</button>
        </form>

        <!-- 注册表单 -->
        <form v-else @submit.prevent="handleRegister">
          <div class="form-group">
            <input v-model="registerForm.username" type="text" placeholder="用户名" required />
          </div>
          <div class="form-group">
            <input v-model="registerForm.email" type="email" placeholder="邮箱" required />
          </div>
          <div class="form-group">
            <input v-model="registerForm.password" type="password" placeholder="密码" required />
          </div>
          <div class="form-group">
            <input
              v-model="registerForm.confirmPassword"
              type="password"
              placeholder="确认密码"
              required
            />
          </div>
          <div v-if="registerError" class="error-message">{{ registerError }}</div>
          <div v-if="passwordMatchError" class="error-message">
            {{ passwordMatchError }}
          </div>
          <button type="submit" class="submit-btn" :disabled="!isRegisterValid">注册</button>
        </form>

        <!-- 切换链接 -->
        <div class="switch-mode">
          <a href="#" @click.prevent="mode = 'login'" v-if="mode === 'register'">
            ← 已有账号？登录
          </a>
          <a href="#" @click.prevent="mode = 'register'" v-else> 没有账号？现在注册 → </a>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from "vue";
import { useUserStore } from "@/store/user";
import { storeToRefs } from "pinia";

const userStore = useUserStore();
const { showLogin } = storeToRefs(userStore);

// 当前模式: login 或 register
const mode = ref<"login" | "register">("login");

// 登录表单数据
const loginForm = reactive({
  username: "",
  password: "",
});
const loginError = ref("");

// 注册表单数据
const registerForm = reactive({
  username: "",
  email: "",
  password: "",
  confirmPassword: "",
});
const registerError = ref("");

// 关闭对话框并重置
const closeDialog = () => {
  userStore.showLogin = false;
  // 重置表单和错误
  loginForm.username = "";
  loginForm.password = "";
  registerForm.username = "";
  registerForm.email = "";
  registerForm.password = "";
  registerForm.confirmPassword = "";
  loginError.value = "";
  registerError.value = "";
  mode.value = "login";
};

// 登录表单有效性检查
const isLoginValid = computed(() => {
  return loginForm.username.trim() !== "" && loginForm.password.trim() !== "";
});

// 密码匹配错误
const passwordMatchError = computed(() => {
  if (registerForm.password && registerForm.confirmPassword) {
    return registerForm.password !== registerForm.confirmPassword ? "两次密码不一致" : "";
  }
  return "";
});

// 注册表单有效性检查（含邮箱格式）
const isRegisterValid = computed(() => {
  return (
    registerForm.username.trim() !== "" &&
    registerForm.email.trim() !== "" &&
    registerForm.password.trim() !== "" &&
    registerForm.confirmPassword.trim() !== "" &&
    registerForm.password === registerForm.confirmPassword &&
    /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(registerForm.email)
  );
});

// 处理登录
const handleLogin = () => {
  const success = userStore.login(loginForm.username, loginForm.password);
  if (success) {
    closeDialog();
  } else {
    loginError.value = "用户名或密码错误";
  }
};

// 处理注册
const handleRegister = () => {
  // 二次验证
  if (registerForm.password !== registerForm.confirmPassword) {
    registerError.value = "密码不一致";
    return;
  }
  const success = userStore.register({
    username: registerForm.username,
    email: registerForm.email,
    password: registerForm.password,
  });
  if (success) {
    closeDialog();
  } else {
    registerError.value = "用户名或邮箱已被注册";
  }
};
</script>

<style scoped>
.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog-card {
  background: white;
  border-radius: 24px;
  padding: 2rem;
  width: 90%;
  max-width: 400px;
  box-shadow: 0 20px 35px -8px rgba(0, 0, 0, 0.2);
  position: relative;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.close-btn {
  position: absolute;
  top: 1rem;
  right: 1rem;
  background: none;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
  color: #666;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}

.close-btn:hover {
  background: #f0f0f0;
}

h3 {
  margin-top: 0;
  margin-bottom: 1.5rem;
  font-size: 1.5rem;
  color: #1a1a1a;
  text-align: center;
}

.form-group {
  margin-bottom: 1.2rem;
}

.form-group input {
  width: 100%;
  padding: 0.8rem 1rem;
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  font-size: 1rem;
  transition: border-color 0.2s;
  box-sizing: border-box;
}

.form-group input:focus {
  outline: none;
  border-color: #3b82f6;
}

.submit-btn {
  width: 100%;
  padding: 0.8rem;
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s;
  margin-top: 0.5rem;
}

.submit-btn:hover {
  opacity: 0.9;
}

.submit-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.error-message {
  color: #dc2626;
  font-size: 0.9rem;
  margin-top: 0.3rem;
  margin-bottom: 0.5rem;
  text-align: center;
}

.switch-mode {
  margin-top: 1.5rem;
  text-align: center;
}

.switch-mode a {
  color: #3b82f6;
  text-decoration: none;
  font-size: 0.95rem;
}

.switch-mode a:hover {
  text-decoration: underline;
}
</style>
