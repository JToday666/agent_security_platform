<template>
  <div class="form-card ui-surface-glass">
    <h1 class="page-title">修改信息</h1>
    <p class="page-subtitle">更新您的个人资料和账户信息。</p>

    <form @submit.prevent="handleSubmit" class="profile-form">
      <!-- 头像上传区域 -->
      <div class="avatar-section ui-surface-white">
        <div class="avatar-preview">
          <img
            :src="avatarPreview || avatarUrl || defaultAvatar"
            alt="头像"
            v-if="avatarPreview || avatarUrl"
          />
          <span v-else class="avatar-placeholder">📷</span>
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
          <div v-if="uploading" class="uploading-hint">上传中..</div>
        </div>
      </div>

      <!-- 表单字段 -->
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
import { ref, reactive, onMounted, watch } from "vue";
import { useUserStore } from "@/store/user";
import { storeToRefs } from "pinia";

const userStore = useUserStore();
const { currentUser, avatarUrl } = storeToRefs(userStore);

// 默认头像，请替换为实际图片地址。
const defaultAvatar = "https://via.placeholder.com/100?text=Avatar";
const MAX_AVATAR_SIZE = 2 * 1024 * 1024;
const ALLOWED_AVATAR_TYPES = ["image/jpeg", "image/png"];

// 表单数据
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

// 从store加载当前用户信息到表单
const loadUserData = () => {
  if (currentUser.value) {
    form.username = currentUser.value.username || "";
    form.email = currentUser.value.email || ""; // 邮箱只读显示，不用于提交
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

const onAvatarChange = async (e: Event) => {
  const target = e.target as HTMLInputElement;
  const file = target.files?.[0];
  if (!file) return;

  if (!ALLOWED_AVATAR_TYPES.includes(file.type)) {
    message.value = "仅支持 JPG、PNG 格式";
    messageType.value = "error";
    target.value = "";
    return;
  }

  if (file.size > MAX_AVATAR_SIZE) {
    message.value = "头像大小不能超过 2MB";
    messageType.value = "error";
    target.value = "";
    return;
  }

  const reader = new FileReader();
  reader.onload = (e) => {
    avatarPreview.value = e.target?.result as string;
  };
  reader.readAsDataURL(file);

  uploading.value = true;
  message.value = "";
  try {
    const newUrl = await userStore.uploadAvatar(file);
    avatarPreview.value = null;
    message.value = "头像更新成功";
    messageType.value = "success";
  } catch (error: any) {
    message.value = error.message || "头像上传失败";
    messageType.value = "error";
    avatarPreview.value = null;
  } finally {
    uploading.value = false;
    target.value = "";
  }
};

const handleSubmit = async () => {
  const normalizedUsername = form.username.trim();

  if (normalizedUsername.length < 3) {
    message.value = "用户名长度至少3位";
    messageType.value = "error";
    return;
  }

  if (form.password && form.password.length < 6) {
    message.value = "密码长度至少6位";
    messageType.value = "error";
    return;
  }

  // 密码一致性验证
  if (form.password && form.password !== form.confirmPassword) {
    message.value = "两次输入的密码不一致";
    messageType.value = "error";
    return;
  }

  // 创建更新数据，只包含可修改字段：用户名、密码
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
    message.value = "没有要保存的修改";
    messageType.value = "error";
    return;
  }

  submitting.value = true;
  message.value = "";

  try {
    await userStore.updateProfile(updateData);
    message.value = "信息更新成功";
    messageType.value = "success";
    form.password = "";
    form.confirmPassword = "";
  } catch (error: any) {
    message.value = error.message || "更新失败";
    messageType.value = "error";
  } finally {
    submitting.value = false;
  }
};

const resetForm = () => {
  loadUserData(); // 重置为store中的原始数据
  form.password = "";
  form.confirmPassword = "";
  avatarPreview.value = null;
  message.value = "";
};
</script>

<style scoped>
/* 全局重置动画 */
.form-card {
  border-radius: 2rem;
  padding: 2.5rem;
  max-width: 600px;
  margin: 0 auto;
}

.page-title {
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.page-subtitle {
  font-size: 1.1rem;
  margin-bottom: 2rem;
}

/* 头像区域 */
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
  font-size: 2rem;
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

/* 表单组 */
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

/* 提示信息 */
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

/* 按钮组 */
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

/* 响应式 */
@media (max-width: 768px) {
  .form-card {
    padding: 1.5rem;
  }

  .avatar-section {
    flex-direction: column;
    text-align: center;
    gap: 1rem;
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
