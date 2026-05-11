<template>
  <div class="content profile-page layout-page-shell layout-page-shell--narrow">
    <PageHero
      :title="t('auth.profile.title')"
      :description="t('auth.profile.description')"
    />

    <div class="profile-grid">
      <aside class="profile-side">
        <div class="avatar-panel">
          <div class="avatar-preview">
            <img
              v-if="(avatarPreview || avatarDisplayUrl) && !hasAvatarError"
              :src="avatarPreview || avatarDisplayUrl"
              :alt="t('auth.profile.avatarAlt')"
              class="avatar-image"
              @error="hasAvatarError = true"
            />
            <span v-else class="default-avatar">{{ usernameInitial }}</span>
          </div>

          <div class="avatar-copy">
            <strong>{{ form.username || t("auth.profile.usernameEmpty") }}</strong>
            <span>{{ form.email || t("auth.profile.emailEmpty") }}</span>
          </div>

          <div class="upload-actions">
            <UiButton
              as="label"
              for="avatar"
              variant="primary"
              leading-icon="lucide:upload"
              :loading="uploading"
            >
              {{ t("auth.profile.selectAvatar") }}
            </UiButton>
            <input
              id="avatar"
              type="file"
              accept="image/*"
              class="hidden-input"
              :disabled="uploading"
              @change="onAvatarChange"
            />
            <p class="hint">{{ t("auth.profile.avatarHint") }}</p>
            <div v-if="uploading" class="uploading-hint">
              {{ t("auth.profile.uploadingAvatar") }}
            </div>
          </div>
        </div>

        <SectionBlock
          :title="t('auth.profile.accountActionsTitle')"
          :description="t('auth.profile.accountActionsDescription')"
        >
          <UiButton
            variant="danger"
            leading-icon="lucide:log-out"
            block
            @click="handleLogoutClick"
          >
            {{ t("auth.profile.logout") }}
          </UiButton>
        </SectionBlock>
      </aside>

      <SectionBlock
        class="profile-main"
        :title="t('auth.profile.updateTitle')"
        :description="t('auth.profile.updateDescription')"
      >
        <InlineNotice
          v-if="message"
          :tone="messageType === 'success' ? 'success' : 'danger'"
          :message="message"
        />

        <form class="profile-form" @submit.prevent="handleSubmit">
          <FormField
            :label="t('auth.fields.username')"
            :model-value="form.username"
            type="text"
            :placeholder="t('auth.placeholders.username')"
            leading-icon="lucide:user"
            @update:model-value="form.username = $event"
          />

          <FormField
            :label="t('auth.fields.email')"
            :model-value="form.email"
            type="email"
            readonly
            :help="t('auth.profile.emailReadonlyHelp')"
            leading-icon="lucide:mail"
            @update:model-value="form.email = $event"
          />

          <FormField
            :label="t('auth.fields.newPassword')"
            :model-value="form.password"
            type="password"
            :placeholder="t('auth.placeholders.newPassword')"
            leading-icon="lucide:lock"
            @update:model-value="form.password = $event"
          />

          <FormField
            :label="t('auth.fields.confirmNewPassword')"
            :model-value="form.confirmPassword"
            type="password"
            :placeholder="t('auth.placeholders.confirmNewPassword')"
            leading-icon="lucide:shield-check"
            @update:model-value="form.confirmPassword = $event"
          />

          <div class="form-actions">
            <UiButton
              type="button"
              variant="secondary"
              leading-icon="lucide:rotate-ccw"
              :disabled="submitting"
              @click="resetForm"
            >
              {{ t("auth.profile.reset") }}
            </UiButton>
            <UiButton
              type="submit"
              variant="primary"
              leading-icon="lucide:save"
              :loading="submitting"
            >
              {{ t("common.actions.saveChanges") }}
            </UiButton>
          </div>
        </form>
      </SectionBlock>
    </div>

    <ConfirmDialog
      v-model="showLogoutConfirm"
      :title="t('auth.profile.logoutConfirmTitle')"
      :message="t('auth.profile.logoutConfirmMessage')"
      :confirm-text="t('auth.profile.logout')"
      :cancel-text="t('common.actions.cancel')"
      :danger="true"
      :loading="logoutLoading"
      @confirm="handleLogoutConfirm"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, reactive, ref, watch } from "vue";
import { storeToRefs } from "pinia";
import { useI18n } from "vue-i18n";
import { useRouter } from "vue-router";
import { RouteLocation } from "@/app/router/route-names";
import { useUserStore } from "@/modules/account/stores/userStore";
import UiButton from "@/shared/ui/actions/UiButton.vue";
import InlineNotice from "@/shared/ui/feedback/InlineNotice.vue";
import ConfirmDialog from "@/shared/ui/feedback/ConfirmDialog.vue";
import FormField from "@/shared/ui/forms/FormField.vue";
import PageHero from "@/shared/ui/page/PageHero.vue";
import SectionBlock from "@/shared/ui/page/SectionBlock.vue";

const userStore = useUserStore();
const router = useRouter();
const { t } = useI18n();
const { avatarDisplayUrl, currentUser } = storeToRefs(userStore);

const MAX_AVATAR_SIZE = 2 * 1024 * 1024;
const ALLOWED_AVATAR_TYPES = ["image/jpeg", "image/png"];
const SUCCESS_MESSAGE_TIMEOUT_MS = 3000;

const form = reactive({
  username: "",
  email: "",
  password: "",
  confirmPassword: "",
});

const avatarPreview = ref<string | null>(null);
const submitting = ref(false);
const uploading = ref(false);
const message = ref("");
const messageType = ref<"success" | "error">("success");
const showLogoutConfirm = ref(false);
const logoutLoading = ref(false);
const hasAvatarError = ref(false);
const usernameInitial = computed(() =>
  (form.username || currentUser.value?.username || "A").trim().charAt(0).toUpperCase() || "A"
);
let messageTimer: number | null = null;

const clearMessageTimer = () => {
  if (messageTimer !== null) {
    window.clearTimeout(messageTimer);
    messageTimer = null;
  }
};

const clearMessage = () => {
  clearMessageTimer();
  message.value = "";
};

const setMessage = (
  nextMessage: string,
  type: "success" | "error",
  autoDismiss = type === "success",
) => {
  clearMessageTimer();
  message.value = nextMessage;
  messageType.value = type;

  if (!nextMessage || !autoDismiss) {
    return;
  }

  messageTimer = window.setTimeout(() => {
    message.value = "";
    messageTimer = null;
  }, SUCCESS_MESSAGE_TIMEOUT_MS);
};

const loadUserData = () => {
  if (currentUser.value) {
    form.username = currentUser.value.username || "";
    form.email = currentUser.value.email || "";
  }
};

onMounted(() => {
  if (currentUser.value) {
    loadUserData();
  } else {
    userStore
      .fetchProfile()
      .then(() => {
        loadUserData();
      })
      .catch(() => {});
  }
});

watch(currentUser, () => {
  loadUserData();
});

onUnmounted(() => {
  clearMessageTimer();
});

const onAvatarChange = async (event: Event) => {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];

  if (!file) {
    return;
  }

  if (!ALLOWED_AVATAR_TYPES.includes(file.type)) {
    setMessage(t("auth.profile.avatarTypeError"), "error", false);
    target.value = "";
    return;
  }

  if (file.size > MAX_AVATAR_SIZE) {
    setMessage(t("auth.profile.avatarSizeError"), "error", false);
    target.value = "";
    return;
  }

  const reader = new FileReader();
  reader.onload = (loadEvent) => {
    avatarPreview.value = loadEvent.target?.result as string;
  };
  reader.readAsDataURL(file);

  uploading.value = true;
  clearMessage();

  try {
    await userStore.uploadAvatar(file);
    avatarPreview.value = null;
    hasAvatarError.value = false;
    setMessage(t("auth.profile.avatarUpdated"), "success");
  } catch (error: any) {
    setMessage(error.message || t("auth.profile.avatarUploadFailed"), "error", false);
    avatarPreview.value = null;
  } finally {
    uploading.value = false;
    target.value = "";
  }
};

const handleSubmit = async () => {
  const normalizedUsername = form.username.trim();

  if (normalizedUsername.length < 3) {
    setMessage(t("auth.profile.usernameMin"), "error", false);
    return;
  }

  if (form.password && form.password.length < 6) {
    setMessage(t("auth.profile.passwordMin"), "error", false);
    return;
  }

  if (form.password && form.password !== form.confirmPassword) {
    setMessage(t("auth.profile.passwordMismatch"), "error", false);
    return;
  }

  const updateData: {
    username?: string;
    password?: string;
  } = {};

  if (normalizedUsername !== currentUser.value?.username) {
    updateData.username = normalizedUsername;
  }

  if (form.password) {
    updateData.password = form.password;
  }

  if (Object.keys(updateData).length === 0) {
    setMessage(t("auth.profile.nothingChanged"), "error", false);
    return;
  }

  submitting.value = true;
  clearMessage();

  try {
    await userStore.updateProfile(updateData);
    setMessage(t("auth.profile.updateSuccess"), "success");
    form.password = "";
    form.confirmPassword = "";
  } catch (error: any) {
    setMessage(error.message || t("auth.profile.updateFailed"), "error", false);
  } finally {
    submitting.value = false;
  }
};

const resetForm = () => {
  loadUserData();
  form.password = "";
  form.confirmPassword = "";
  avatarPreview.value = null;
  clearMessage();
};

const handleLogoutClick = () => {
  showLogoutConfirm.value = true;
};

const handleLogoutConfirm = () => {
  logoutLoading.value = true;

  window.setTimeout(() => {
    userStore.logout();
    void router.push(RouteLocation.home);
    showLogoutConfirm.value = false;
    logoutLoading.value = false;
  }, 100);
};
</script>

<style scoped lang="scss">
.profile-page {
  padding-bottom: 2.5rem;
}

.profile-grid {
  display: grid;
  grid-template-columns: minmax(280px, 0.82fr) minmax(0, 1.18fr);
  gap: 2rem;
  align-items: start;
  min-width: 0;
}

.profile-side {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  min-width: 0;
}

.avatar-panel {
  padding: 1.8rem 1.4rem;
  border-radius: var(--radius-card-sm);
  background: var(--color-surface);
  border: 1px solid var(--color-border-soft);
  box-shadow: var(--shadow-surface-soft);
  transition: box-shadow var(--duration-base) var(--ease-spring);
  position: relative;
}

.avatar-panel::before {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: inherit;
  box-shadow: var(--glass-border-inset);
  pointer-events: none;
}

.avatar-panel:hover {
  box-shadow: var(--shadow-surface-hover);
}

.avatar-preview {
  width: 110px;
  height: 110px;
  margin: 0 auto;
  border-radius: 50%;
  background: var(--color-surface-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border: 3px solid rgba(255, 255, 255, 0.92);
  box-shadow: 0 18px 28px -20px rgba(79, 70, 229, 0.32);
  transition: transform var(--duration-base) var(--ease-spring), box-shadow var(--duration-base) var(--ease-spring);
}

.avatar-preview:hover {
  transform: translateY(-4px) scale(1.02);
  box-shadow: 0 22px 34px -22px rgba(79, 70, 229, 0.45);
}

.avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.default-avatar {
  width: 100%;
  height: 100%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  text-transform: uppercase;
  font-size: 2.75rem;
  color: #fff;
  background: var(--color-primary);
  font-weight: 700;
}

.avatar-placeholder {
  width: 2rem;
  height: 2rem;
  color: #94a3b8;
}

.avatar-copy {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.28rem;
  margin-top: 1rem;
  text-align: center;
}

.avatar-copy strong {
  color: var(--color-text-dark);
  font-size: 1.04rem;
  overflow-wrap: anywhere;
}

.avatar-copy span {
  color: var(--color-text-subtle);
  font-size: 0.9rem;
  overflow-wrap: anywhere;
}

.upload-actions {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--color-border-soft);
}

.hidden-input {
  display: none;
}

.hint,
.uploading-hint {
  margin: 0.55rem 0 0;
  text-align: center;
  color: var(--color-text-subtle);
  font-size: 0.84rem;
  line-height: 1.6;
}

.profile-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  min-width: 0;
}

.form-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.8rem;
  margin-top: 0.75rem;
  padding-top: 1.25rem;
  border-top: 1px solid var(--color-border-soft);
  justify-content: flex-end;
}

@media (max-width: 900px) {
  .profile-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .form-actions {
    flex-direction: column;
  }

  .form-actions :deep(.ui-button) {
    width: 100%;
  }
}
</style>
