<template>
  <Teleport to="body">
    <Transition name="fade" @after-leave="afterLeave">
      <div
        v-if="showLogin"
        class="dialog-overlay ui-modal-overlay"
        @click.self="closeDialog"
      >
        <Transition name="scale" appear>
          <div class="dialog-card ui-modal-card">
            <!-- 关闭按钮 -->
            <button class="close-btn" @click="closeDialog" aria-label="关闭">
              <AppIcon icon="lucide:x" class="close-icon" />
            </button>

            <!-- 标题 & 装饰 -->
            <div class="header">
              <div class="logo-wrapper">
                <AppIcon icon="lucide:shield-check" class="logo-icon" />
              </div>
              <h3>{{ mode === "login" ? "欢迎回来" : "创建账号" }}</h3>
              <p class="subtitle">
                {{
                  mode === "login"
                    ? "登录以继续使用智能体检测平台"
                    : "注册后即可开始检测您的智能体"
                }}
              </p>
            </div>

            <!-- 登录表单 -->
            <form
              v-if="mode === 'login'"
              @submit.prevent="handleLogin"
              class="form"
            >
              <div
                class="form-group"
                :class="{ focused: focusedField === 'login-username' }"
              >
                <AppIcon icon="lucide:user" class="input-icon" />
                <input
                  v-model="loginForm.username"
                  type="text"
                  placeholder="用户名/邮箱"
                  required
                  @focus="focusedField = 'login-username'"
                  @blur="focusedField = null"
                />
              </div>
              <div
                class="form-group"
                :class="{ focused: focusedField === 'login-password' }"
              >
                <AppIcon icon="lucide:lock" class="input-icon" />
                <input
                  v-model="loginForm.password"
                  type="password"
                  placeholder="密码"
                  required
                  @focus="focusedField = 'login-password'"
                  @blur="focusedField = null"
                />
              </div>

              <!-- 密码长度提示 -->
              <div
                v-if="loginForm.password && loginForm.password.length < 6"
                class="error-message"
              >
                密码长度至少6位
              </div>

              <Transition name="shake">
                <div
                  v-if="loginError"
                  class="error-message error-message--stacked"
                >
                  <AppIcon icon="lucide:circle-alert" class="error-icon" />
                  <span class="error-text">{{ loginError }}</span>
                </div>
              </Transition>

              <button
                type="submit"
                class="submit-btn ui-btn"
                :disabled="!isLoginValid || loading"
              >
                <span v-if="!loading">登录</span>
                <span v-else class="loader ui-loader"></span>
              </button>
            </form>

            <!-- 注册表单 -->
            <form v-else @submit.prevent="handleRegister" class="form">
              <div
                class="form-group"
                :class="{ focused: focusedField === 'reg-username' }"
              >
                <AppIcon icon="lucide:user" class="input-icon" />
                <input
                  v-model="registerForm.username"
                  type="text"
                  placeholder="用户名"
                  required
                  @focus="focusedField = 'reg-username'"
                  @blur="focusedField = null"
                />
              </div>
              <div
                v-if="
                  registerForm.username &&
                  registerForm.username.trim().length < 3
                "
                class="error-message"
              >
                用户名长度至少3位
              </div>
              <div
                class="form-group"
                :class="{ focused: focusedField === 'reg-email' }"
              >
                <AppIcon icon="lucide:mail" class="input-icon" />
                <input
                  v-model="registerForm.email"
                  type="email"
                  placeholder="邮箱"
                  required
                  @focus="focusedField = 'reg-email'"
                  @blur="focusedField = null"
                />
              </div>
              <div
                class="form-group"
                :class="{ focused: focusedField === 'reg-password' }"
              >
                <AppIcon icon="lucide:lock" class="input-icon" />
                <input
                  v-model="registerForm.password"
                  type="password"
                  placeholder="密码"
                  required
                  @focus="focusedField = 'reg-password'"
                  @blur="focusedField = null"
                />
              </div>
              <!-- 密码长度提示 -->
              <div
                v-if="registerForm.password && registerForm.password.length < 6"
                class="error-message"
              >
                密码长度至少6位
              </div>
              <div
                class="form-group"
                :class="{ focused: focusedField === 'reg-confirm' }"
              >
                <AppIcon icon="lucide:lock" class="input-icon" />
                <input
                  v-model="registerForm.confirmPassword"
                  type="password"
                  placeholder="确认密码"
                  required
                  @focus="focusedField = 'reg-confirm'"
                  @blur="focusedField = null"
                />
              </div>

              <Transition name="shake">
                <div
                  v-if="registerError"
                  class="error-message error-message--stacked"
                >
                  <AppIcon icon="lucide:circle-alert" class="error-icon" />
                  <span class="error-text">{{ registerError }}</span>
                </div>
              </Transition>
              <Transition name="shake">
                <div
                  v-if="passwordMatchError"
                  class="error-message error-message--stacked"
                >
                  <AppIcon icon="lucide:circle-alert" class="error-icon" />
                  <span class="error-text">{{ passwordMatchError }}</span>
                </div>
              </Transition>

              <button
                type="submit"
                class="submit-btn ui-btn"
                :disabled="!isRegisterValid || loading"
              >
                <span v-if="!loading">注册</span>
                <span v-else class="loader ui-loader"></span>
              </button>
            </form>

            <!-- 切换模式链接 -->
            <div class="switch-mode">
              <a href="#" @click.prevent="toggleMode">
                <span v-if="mode === 'register'">← 已有账号？</span>
                <span v-else>没有账号？</span>
                <span class="highlight">{{
                  mode === "register" ? "登录" : "立即注册"
                }}</span>
                <span v-if="mode === 'login'"> →</span>
              </a>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from "vue";
import { useUserStore } from "@/store/user";
import { storeToRefs } from "pinia";
import AppIcon from "@/components/AppIcon.vue";

const userStore = useUserStore();
const { showLogin } = storeToRefs(userStore);

const mode = ref<"login" | "register">("login");
const loading = ref(false);
const focusedField = ref<string | null>(null);

const loginForm = reactive({
  username: "",
  password: "",
});
const loginError = ref("");

const registerForm = reactive({
  username: "",
  email: "",
  password: "",
  confirmPassword: "",
});
const registerError = ref("");

const afterLeave = () => {
  // 重置所有状态
  loginForm.username = "";
  loginForm.password = "";
  registerForm.username = "";
  registerForm.email = "";
  registerForm.password = "";
  registerForm.confirmPassword = "";
  loginError.value = "";
  registerError.value = "";
  mode.value = "login";
  loading.value = false;
};

const closeDialog = () => {
  userStore.showLogin = false;
};

const toggleMode = () => {
  mode.value = mode.value === "login" ? "register" : "login";
  loginError.value = "";
  registerError.value = "";
};

// 登录表单验证：用户名不为空，密码长度 >=6
const isLoginValid = computed(() => {
  return loginForm.username.trim() !== "" && loginForm.password.length >= 6;
});

// 密码一致错误
const passwordMatchError = computed(() => {
  if (registerForm.password && registerForm.confirmPassword) {
    return registerForm.password !== registerForm.confirmPassword
      ? "两次密码不一致"
      : "";
  }
  return "";
});

// 注册表单验证
const isRegisterValid = computed(() => {
  const normalizedUsername = registerForm.username.trim();
  return (
    normalizedUsername.length >= 3 &&
    registerForm.email.trim() !== "" &&
    registerForm.password.length >= 6 &&
    registerForm.confirmPassword.length >= 6 &&
    registerForm.password === registerForm.confirmPassword &&
    /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(registerForm.email)
  );
});

const handleLogin = async () => {
  if (loginForm.password.length < 6) {
    loginError.value = "密码长度至少6位";
    return;
  }
  loading.value = true;
  loginError.value = "";
  try {
    const success = await userStore.login(
      loginForm.username,
      loginForm.password,
    );
    if (success) {
      closeDialog();
    } else {
      loginError.value = "登录失败，请稍后重试"; // 实际上异常会被 catch
    }
  } catch (error: any) {
    loginError.value = error.message || "用户名/邮箱或密码错误";
  } finally {
    loading.value = false;
  }
};

const handleRegister = async () => {
  if (registerForm.username.trim().length < 3) {
    registerError.value = "用户名长度至少3位";
    return;
  }
  if (registerForm.password.length < 6) {
    registerError.value = "密码长度至少6位";
    return;
  }
  if (registerForm.password !== registerForm.confirmPassword) {
    registerError.value = "密码不一致";
    return;
  }
  loading.value = true;
  registerError.value = "";
  try {
    const success = await userStore.register({
      username: registerForm.username.trim(),
      email: registerForm.email.trim(),
      password: registerForm.password,
    });
    if (success) {
      closeDialog();
    } else {
      registerError.value = "注册失败，请稍后重试";
    }
  } catch (error: any) {
    registerError.value = error.message || "用户名或邮箱已被注册";
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
/* 过渡动画 */
.shake-enter-active {
  animation: shake 0.3s ease;
}

@keyframes shake {
  0%,
  100% {
    transform: translateX(0);
  }

  20% {
    transform: translateX(-5px);
  }

  40% {
    transform: translateX(5px);
  }

  60% {
    transform: translateX(-3px);
  }

  80% {
    transform: translateX(3px);
  }
}

.dialog-overlay {
  background-color: var(--overlay-dark-60);
  backdrop-filter: blur(var(--blur-8));
  z-index: var(--z-nav);
}

.dialog-card {
  background: var(--glass-bg-95);
  backdrop-filter: blur(var(--blur-10));
  padding: 2rem 2rem 2rem 2rem;
  max-width: 420px;
  box-shadow:
    0 25px 50px -12px rgba(0, 0, 0, 0.25),
    0 0 0 1px rgba(255, 255, 255, 0.5) inset;
}

.close-btn {
  position: absolute;
  top: 1rem;
  right: 1rem;
  background: rgba(0, 0, 0, 0.05);
  border: none;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s;
}

.close-btn:hover {
  background: rgba(0, 0, 0, 0.1);
  color: #0f172a;
  transform: rotate(90deg);
}

.close-icon {
  width: 1.25rem;
  height: 1.25rem;
}

.header {
  text-align: center;
  margin-bottom: 2rem;
}

.logo-wrapper {
  display: inline-flex;
  padding: 12px;
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  border-radius: 24px;
  margin-bottom: 1rem;
  box-shadow: 0 10px 15px -3px rgba(37, 99, 235, 0.2);
}

.logo-icon {
  width: 32px;
  height: 32px;
  color: white;
}

h3 {
  margin: 0;
  font-size: 1.8rem;
  font-weight: 700;
  background: linear-gradient(135deg, #1e293b, #0f172a);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.subtitle {
  margin: 0.5rem 0 0;
  color: #64748b;
  font-size: 0.9rem;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 1.2rem;
}

.form-group {
  position: relative;
  transition: all 0.2s;
}

.form-group.focused .input-icon {
  color: #3b82f6;
}

.input-icon {
  position: absolute;
  left: 14px;
  top: 50%;
  transform: translateY(-50%);
  width: 18px;
  height: 18px;
  color: #94a3b8;
  transition: color 0.2s;
  pointer-events: none;
}

.form-group input {
  width: 100%;
  padding: 0.9rem 1rem 0.9rem 2.8rem;
  border: 2px solid #e2e8f0;
  border-radius: 18px;
  font-size: 1rem;
  background: white;
  transition:
    border-color 0.2s,
    box-shadow 0.2s;
  outline: none;
}

.form-group.focused input {
  border-color: #3b82f6;
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.15);
}

.submit-btn {
  position: relative;
  width: 100%;
  padding: 0.9rem;
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: white;
  border: none;
  border-radius: 18px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  overflow: hidden;
  transition: all 0.2s;
  margin-top: 0.5rem;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px -10px #3b82f6;
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error-message {
  display: flex;
  align-items: center;
  gap: 6px;
  justify-content: center;
  color: #dc2626;
  font-size: 0.85rem;
  background: #fee2e2;
  padding: 0.5rem 1rem;
  border-radius: 30px;
  margin-top: -0.5rem;
}

.error-message--stacked {
  flex-direction: column;
  gap: 0.35rem;
  text-align: center;
  line-height: 1.45;
  padding: 0.65rem 0.9rem;
  border-radius: 16px;
  max-width: 100%;
}

.error-icon {
  width: 14px;
  height: 14px;
  color: #ef4444;
  flex-shrink: 0;
}

.error-text {
  display: block;
  max-width: 100%;
  word-break: break-word;
}

.switch-mode {
  margin-top: 1.5rem;
  text-align: center;
}

.switch-mode a {
  color: #64748b;
  text-decoration: none;
  font-size: 0.95rem;
  transition: color 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.switch-mode a:hover {
  color: #3b82f6;
}

.highlight {
  color: #3b82f6;
  font-weight: 600;
}
</style>
