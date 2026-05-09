<template>
  <div class="content profile-page layout-page-shell layout-page-shell--narrow">
    <PageHero
      title="个人资料"
      description="管理头像、用户名和密码。"
    />

    <div class="profile-grid">
      <aside class="profile-side">
        <div class="avatar-panel">
          <div class="avatar-preview">
            <img
              v-if="(avatarPreview || avatarDisplayUrl) && !hasAvatarError"
              :src="avatarPreview || avatarDisplayUrl"
              alt="头像"
              class="avatar-image"
              @error="hasAvatarError = true"
            />
            <span v-else class="default-avatar">{{ usernameInitial }}</span>
          </div>

          <div class="avatar-copy">
            <strong>{{ form.username || "未设置用户名" }}</strong>
            <span>{{ form.email || "未绑定邮箱" }}</span>
          </div>

          <div class="upload-actions">
            <UiButton
              as="label"
              for="avatar"
              variant="primary"
              leading-icon="lucide:upload"
              :loading="uploading"
            >
              选择新头像
            </UiButton>
            <input
              id="avatar"
              type="file"
              accept="image/*"
              class="hidden-input"
              :disabled="uploading"
              @change="onAvatarChange"
            />
            <p class="hint">支持 JPG、PNG，大小不超过 2MB。</p>
            <div v-if="uploading" class="uploading-hint">正在上传头像...</div>
          </div>
        </div>

        <SectionBlock
          title="账号操作"
          description="退出后需要重新登录才能继续访问工作台。"
        >
          <UiButton
            variant="danger"
            leading-icon="lucide:log-out"
            block
            @click="handleLogoutClick"
          >
            退出登录
          </UiButton>
        </SectionBlock>
      </aside>

      <SectionBlock
        class="profile-main"
        title="更新账号信息"
        description="邮箱不可修改，您可以修改用户名与密码。"
      >
        <InlineNotice
          v-if="message"
          :tone="messageType === 'success' ? 'success' : 'danger'"
          :message="message"
        />

        <form class="profile-form" @submit.prevent="handleSubmit">
          <FormField
            label="用户名"
            :model-value="form.username"
            type="text"
            placeholder="请输入用户名"
            leading-icon="lucide:user"
            @update:model-value="form.username = $event"
          />

          <FormField
            label="邮箱"
            :model-value="form.email"
            type="email"
            readonly
            help="邮箱不可修改。"
            leading-icon="lucide:mail"
            @update:model-value="form.email = $event"
          />

          <FormField
            label="新密码"
            :model-value="form.password"
            type="password"
            placeholder="留空表示不修改"
            leading-icon="lucide:lock"
            @update:model-value="form.password = $event"
          />

          <FormField
            label="确认新密码"
            :model-value="form.confirmPassword"
            type="password"
            placeholder="再次输入新密码"
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
              取消
            </UiButton>
            <UiButton
              type="submit"
              variant="primary"
              leading-icon="lucide:save"
              :loading="submitting"
            >
              保存修改
            </UiButton>
          </div>
        </form>
      </SectionBlock>
    </div>

    <ConfirmDialog
      v-model="showLogoutConfirm"
      title="确认退出登录"
      message="确定退出当前账号吗？"
      confirm-text="退出登录"
      cancel-text="取消"
      :danger="true"
      :loading="logoutLoading"
      @confirm="handleLogoutConfirm"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, reactive, ref, watch } from "vue";
import { storeToRefs } from "pinia";
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
    setMessage("仅支持 JPG、PNG 格式", "error", false);
    target.value = "";
    return;
  }

  if (file.size > MAX_AVATAR_SIZE) {
    setMessage("头像大小不能超过 2MB", "error", false);
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
    setMessage("头像更新成功", "success");
  } catch (error: any) {
    setMessage(error.message || "头像上传失败", "error", false);
    avatarPreview.value = null;
  } finally {
    uploading.value = false;
    target.value = "";
  }
};

const handleSubmit = async () => {
  const normalizedUsername = form.username.trim();

  if (normalizedUsername.length < 3) {
    setMessage("用户名长度至少 3 位", "error", false);
    return;
  }

  if (form.password && form.password.length < 6) {
    setMessage("密码长度至少 6 位", "error", false);
    return;
  }

  if (form.password && form.password !== form.confirmPassword) {
    setMessage("两次输入的密码不一致", "error", false);
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
    setMessage("没有要保存的修改", "error", false);
    return;
  }

  submitting.value = true;
  clearMessage();

  try {
    await userStore.updateProfile(updateData);
    setMessage("信息更新成功", "success");
    form.password = "";
    form.confirmPassword = "";
  } catch (error: any) {
    setMessage(error.message || "更新失败", "error", false);
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
