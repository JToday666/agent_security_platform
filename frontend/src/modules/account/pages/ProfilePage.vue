<template>
  <div class="content form-card layout-page-panel layout-page-panel--sm ui-surface-glass">
    <h1 class="page-title layout-page-title">修改信息</h1>
    <p class="page-subtitle layout-page-subtitle">更新您的个人资料和账户信息。</p>

    <form @submit.prevent="handleSubmit" class="profile-form">
      <div class="avatar-section ui-surface-white">
        <div class="avatar-preview">
          <img
            :src="avatarPreview || avatarDisplayUrl"
            alt="头像"
            v-if="avatarPreview || avatarDisplayUrl"
          />
          <AppIcon v-else icon="lucide:image-plus" class="avatar-placeholder" />
        </div>
        <div class="avatar-upload">
          <label
            for="avatar"
            class="upload-label ui-btn ui-btn-pill ui-btn-gradient ui-btn-hover-lift"
            >选择新头像</label
          >
          <input
            type="file"
            id="avatar"
            accept="image/*"
            @change="onAvatarChange"
            class="hidden-input"
            :disabled="uploading"
          />
          <p class="hint">支持 JPG、PNG，大小不超过 2MB</p>
          <div v-if="uploading" class="uploading-hint">上传中...</div>
        </div>
      </div>

      <div class="form-group">
        <label for="username">用户名</label>
        <input
          type="text"
          id="username"
          class="ui-input-pill ui-input-focus-ring"
          v-model="form.username"
          placeholder="请输入用户名"
          required
        />
      </div>

      <div class="form-group">
        <label for="email">邮箱</label>
        <input
          type="email"
          id="email"
          v-model="form.email"
          readonly
          class="readonly-field ui-input-pill ui-input-focus-ring"
        />
        <p class="field-hint">邮箱不可修改</p>
      </div>

      <div class="form-group">
        <label for="password">新密码</label>
        <input
          type="password"
          id="password"
          class="ui-input-pill ui-input-focus-ring"
          v-model="form.password"
          placeholder="留空表示不修改"
        />
      </div>

      <div class="form-group">
        <label for="confirmPassword">确认新密码</label>
        <input
          type="password"
          id="confirmPassword"
          class="ui-input-pill ui-input-focus-ring"
          v-model="form.confirmPassword"
          placeholder="再次输入新密码"
        />
      </div>

      <div v-if="message" class="form-message" :class="messageType">
        {{ message }}
      </div>

      <div class="form-actions">
        <button
          type="submit"
          class="submit-btn ui-btn ui-btn-pill ui-btn-gradient ui-btn-hover-lift"
          :disabled="submitting"
        >
          {{ submitting ? "保存中..." : "保存修改" }}
        </button>
        <button
          type="button"
          class="cancel-btn ui-btn ui-btn-pill ui-btn-outline"
          @click="resetForm"
          :disabled="submitting"
        >
          取消
        </button>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, reactive, ref, watch } from "vue";
import { useUserStore } from "@/modules/account/stores/UserStore";
import { storeToRefs } from "pinia";
import AppIcon from "@/shared/ui/AppIcon.vue";

const userStore = useUserStore();
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

const onAvatarChange = async (e: Event) => {
  const target = e.target as HTMLInputElement;
  const file = target.files?.[0];
  if (!file) return;

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
  reader.onload = (e) => {
    avatarPreview.value = e.target?.result as string;
  };
  reader.readAsDataURL(file);

  uploading.value = true;
  clearMessage();
  try {
    await userStore.uploadAvatar(file);
    avatarPreview.value = null;
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
    setMessage("用户名长度至少3位", "error", false);
    return;
  }

  if (form.password && form.password.length < 6) {
    setMessage("密码长度至少6位", "error", false);
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
</script>

<style scoped>
.avatar-section {
  display: flex;
  gap: 2rem;
  align-items: center;
  margin-bottom: 2rem;
  padding: 1.5rem;
  border-radius: 1.2rem;
}

.avatar-preview {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: #f1f5f9;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border: 2px solid #fff;
  box-shadow: 0 5px 10px rgba(0, 0, 0, 0.05);
}

.avatar-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  width: 2rem;
  height: 2rem;
  color: #94a3b8;
}

.avatar-upload {
  flex: 1;
}

.upload-label {
  display: inline-block;
  padding: 0.5rem 1.5rem;
  font-weight: 500;
  transition:
    transform 0.2s,
    box-shadow 0.2s;
  margin-bottom: 0.5rem;
  border: none;
  font-size: 0.95rem;
}

.hidden-input {
  display: none;
}

.hint {
  font-size: 0.85rem;
  color: #64748b;
  margin: 0;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #334155;
}

.form-group input {
  width: 100%;
  padding: 0.8rem 1.2rem;
  font-size: 1rem;
  transition:
    border-color 0.2s,
    box-shadow 0.2s;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
}

.form-group input::placeholder {
  color: #94a3b8;
}

.form-message {
  padding: 0.8rem 1.2rem;
  border-radius: 30px;
  margin-bottom: 1.5rem;
  text-align: center;
  font-size: 0.95rem;
}

.form-message.success {
  background: #dcfce7;
  color: #166534;
  border: 1px solid #86efac;
}

.form-message.error {
  background: #fee2e2;
  color: #991b1b;
  border: 1px solid #fca5a5;
}

.form-actions {
  display: flex;
  gap: 1rem;
  margin-top: 1rem;
}

.submit-btn,
.cancel-btn {
  padding: 0.8rem 2rem;
  border: none;
  font-size: 1rem;
  transition:
    transform 0.2s,
    box-shadow 0.2s;
  flex: 1;
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.cancel-btn:hover {
  background: #f8fafc;
  border-color: #94a3b8;
  transform: translateY(-2px);
  box-shadow: 0 8px 16px -6px rgba(0, 0, 0, 0.1);
}

@media (max-width: 768px) {
  .avatar-section {
    flex-direction: column;
    text-align: center;
    gap: 1rem;
  }

  .form-actions {
    flex-direction: column;
  }
}

.uploading-hint {
  color: #666;
  font-size: 0.85rem;
  margin-top: 0.25rem;
}

.readonly-field {
  background-color: #f5f5f5;
  cursor: not-allowed;
  color: #666;
}

.field-hint {
  font-size: 0.8rem;
  color: #999;
  margin-top: 0.25rem;
}
</style>
