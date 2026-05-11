<template>
  <Teleport to="body">
    <Transition name="fade" @after-leave="afterLeave">
      <div
        v-if="showLogin"
        class="dialog-overlay ui-modal-overlay"
        @click.self="closeDialog"
        @keydown.esc="closeDialog"
      >
        <Transition name="scale" appear>
          <div class="dialog-card ui-modal-card">
            <button
              class="close-btn"
              @click="closeDialog"
              :aria-label="t('common.actions.close')"
            >
              <AppIcon icon="lucide:x" class="close-icon" />
            </button>

            <div class="header">
              <div class="logo-wrapper">
                <AppIcon icon="lucide:shield-check" class="logo-icon" />
              </div>
              <h3>
                {{
                  mode === "login"
                    ? t("auth.dialog.loginTitle")
                    : t("auth.dialog.registerTitle")
                }}
              </h3>
              <p class="subtitle">
                {{
                  mode === "login"
                    ? t("auth.dialog.loginSubtitle")
                    : t("auth.dialog.registerSubtitle")
                }}
              </p>
            </div>

            <form v-if="mode === 'login'" class="form" @submit.prevent="handleLogin">
              <FormField
                :label="t('auth.fields.usernameOrEmail')"
                :model-value="loginForm.username"
                type="text"
                :placeholder="t('auth.placeholders.usernameOrEmail')"
                leading-icon="lucide:user"
                @update:model-value="loginForm.username = $event"
              />
              <FormField
                :label="t('auth.fields.password')"
                :model-value="loginForm.password"
                type="password"
                :placeholder="t('auth.placeholders.password')"
                leading-icon="lucide:lock"
                @update:model-value="loginForm.password = $event"
              />

              <InlineNotice
                v-if="loginForm.password && loginForm.password.length < 6"
                tone="warning"
                :message="t('auth.validation.passwordMin')"
              />
              <InlineNotice v-if="loginError" tone="danger" :message="loginError" />

              <UiButton type="submit" variant="primary" :loading="loading" :disabled="!isLoginValid" block>
                {{ t("auth.dialog.switchToLogin") }}
              </UiButton>
            </form>

            <form v-else class="form" @submit.prevent="handleRegister">
              <FormField
                :label="t('auth.fields.username')"
                :model-value="registerForm.username"
                type="text"
                :placeholder="t('auth.placeholders.username')"
                leading-icon="lucide:user"
                @update:model-value="registerForm.username = $event"
              />
              <InlineNotice
                v-if="registerForm.username && registerForm.username.trim().length < 3"
                tone="warning"
                :message="t('auth.validation.usernameMin')"
              />
              <FormField
                :label="t('auth.fields.email')"
                :model-value="registerForm.email"
                type="email"
                :placeholder="t('auth.placeholders.email')"
                leading-icon="lucide:mail"
                @update:model-value="registerForm.email = $event"
              />
              <FormField
                :label="t('auth.fields.password')"
                :model-value="registerForm.password"
                type="password"
                :placeholder="t('auth.placeholders.password')"
                leading-icon="lucide:lock"
                @update:model-value="registerForm.password = $event"
              />
              <FormField
                :label="t('auth.fields.confirmPassword')"
                :model-value="registerForm.confirmPassword"
                type="password"
                :placeholder="t('auth.placeholders.confirmPassword')"
                leading-icon="lucide:shield-check"
                @update:model-value="registerForm.confirmPassword = $event"
              />

              <InlineNotice
                v-if="registerForm.password && registerForm.password.length < 6"
                tone="warning"
                :message="t('auth.validation.passwordMin')"
              />
              <InlineNotice v-if="registerError" tone="danger" :message="registerError" />
              <InlineNotice
                v-if="passwordMatchError"
                tone="danger"
                :message="passwordMatchError"
              />

              <UiButton type="submit" variant="primary" :loading="loading" :disabled="!isRegisterValid" block>
                {{ t("auth.dialog.switchToRegister") }}
              </UiButton>
            </form>

            <div class="switch-mode">
              <a href="#" @click.prevent="toggleMode">
                <span v-if="mode === 'register'">
                  {{ t("auth.dialog.alreadyHaveAccount") }}
                </span>
                <span v-else>{{ t("auth.dialog.noAccount") }}</span>
                <span class="highlight">
                  {{
                    mode === "register"
                      ? t("auth.dialog.switchToLogin")
                      : t("auth.dialog.switchToRegister")
                  }}
                </span>
              </a>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from "vue";
import { useI18n } from "vue-i18n";
import { useRouter } from "vue-router";
import { storeToRefs } from "pinia";
import { RouteLocation } from "@/app/router/route-names";
import { useUserStore } from "@/modules/account/stores/userStore";
import AppIcon from "@/shared/ui/branding/AppIcon.vue";
import FormField from "@/shared/ui/forms/FormField.vue";
import InlineNotice from "@/shared/ui/feedback/InlineNotice.vue";
import UiButton from "@/shared/ui/actions/UiButton.vue";

const router = useRouter();
const { t } = useI18n();
const userStore = useUserStore();
const { showLogin } = storeToRefs(userStore);

const mode = ref<"login" | "register">("login");
const loading = ref(false);

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

const isLoginValid = computed(() => {
  return loginForm.username.trim() !== "" && loginForm.password.length >= 6;
});

const passwordMatchError = computed(() => {
  if (registerForm.password && registerForm.confirmPassword) {
    return registerForm.password !== registerForm.confirmPassword
      ? t("auth.validation.passwordMismatch")
      : "";
  }
  return "";
});

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
    loginError.value = t("auth.validation.passwordMin");
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
      const redirect = userStore.consumePostLoginRedirect() || RouteLocation.userCenter;
      await router.push(redirect);
    } else {
      loginError.value = t("auth.messages.loginFailed");
    }
  } catch (error: any) {
    loginError.value = error.message || t("auth.messages.loginInvalid");
  } finally {
    loading.value = false;
  }
};

const handleRegister = async () => {
  if (registerForm.username.trim().length < 3) {
    registerError.value = t("auth.validation.usernameMin");
    return;
  }
  if (registerForm.password.length < 6) {
    registerError.value = t("auth.validation.passwordMin");
    return;
  }
  if (registerForm.password !== registerForm.confirmPassword) {
    registerError.value = t("auth.validation.passwordMismatchShort");
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
      const redirect = userStore.consumePostLoginRedirect() || RouteLocation.userCenter;
      await router.push(redirect);
    } else {
      registerError.value = t("auth.messages.registerFailed");
    }
  } catch (error: any) {
    registerError.value = error.message || t("auth.messages.registerConflict");
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped lang="scss">
.dialog-overlay {
  background-color: var(--overlay-dark-60);
  backdrop-filter: blur(var(--blur-8));
  z-index: var(--z-nav);
}

.dialog-card {
  background: var(--glass-bg-95);
  backdrop-filter: blur(var(--blur-10));
  padding: 2rem;
  max-width: 460px;
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
  margin-bottom: 1.5rem;
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
  font-size: 0.92rem;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.switch-mode {
  margin-top: 1.2rem;
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
