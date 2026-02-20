<template>
  <Navbar />
  <main class="page-container profile-page">
    <UserSidebar />
    <div class="content-area">
      <div class="form-card">
        <h1 class="page-title">修改信息</h1>
        <p class="page-subtitle">更新您的个人资料和账户信息。</p>

        <form @submit.prevent="handleSubmit" class="profile-form">
          <!-- 头像上传区域（模拟） -->
          <div class="avatar-section">
            <div class="avatar-preview">
              <img :src="avatarPreview" alt="头像" v-if="avatarPreview" />
              <span v-else class="avatar-placeholder">📷</span>
            </div>
            <div class="avatar-upload">
              <label for="avatar" class="upload-label">选择新头像</label>
              <input
                type="file"
                id="avatar"
                accept="image/*"
                @change="onAvatarChange"
                class="hidden-input"
              />
              <p class="hint">支持 JPG、PNG，大小不超过 2MB</p>
            </div>
          </div>

          <!-- 表单字段 -->
          <div class="form-group">
            <label for="nickname">昵称</label>
            <input
              type="text"
              id="nickname"
              v-model="form.nickname"
              placeholder="请输入昵称"
              required
            />
          </div>

          <div class="form-group">
            <label for="email">邮箱</label>
            <input type="email" id="email" v-model="form.email" placeholder="请输入邮箱" required />
          </div>

          <div class="form-group">
            <label for="password">新密码</label>
            <input
              type="password"
              id="password"
              v-model="form.password"
              placeholder="留空表示不修改"
            />
          </div>

          <div class="form-group">
            <label for="confirmPassword">确认新密码</label>
            <input
              type="password"
              id="confirmPassword"
              v-model="form.confirmPassword"
              placeholder="再次输入新密码"
            />
          </div>

          <div v-if="message" class="form-message" :class="messageType">
            {{ message }}
          </div>

          <div class="form-actions">
            <button type="submit" class="submit-btn" :disabled="submitting">
              {{ submitting ? "保存中..." : "保存修改" }}
            </button>
            <button type="button" class="cancel-btn" @click="resetForm">取消</button>
          </div>
        </form>
      </div>
    </div>
  </main>
</template>

<script setup lang="ts">
import { ref, reactive } from "vue";
import Navbar from "@/components/NavBar.vue";
import UserSidebar from "@/components/UserSidebar.vue";

// 表单数据
const form = reactive({
  nickname: "当前用户",
  email: "user@example.com",
  password: "",
  confirmPassword: "",
});

const avatarPreview = ref<string | null>(null);
const submitting = ref(false);
const message = ref("");
const messageType = ref<"success" | "error">("success");

const onAvatarChange = (e: Event) => {
  const target = e.target as HTMLInputElement;
  const file = target.files?.[0];
  if (file) {
    if (file.size > 2 * 1024 * 1024) {
      message.value = "头像大小不能超过 2MB";
      messageType.value = "error";
      return;
    }
    const reader = new FileReader();
    reader.onload = (e) => {
      avatarPreview.value = e.target?.result as string;
    };
    reader.readAsDataURL(file);
  }
};

const handleSubmit = async () => {
  if (form.password && form.password !== form.confirmPassword) {
    message.value = "两次输入的密码不一致";
    messageType.value = "error";
    return;
  }

  submitting.value = true;
  message.value = "";

  setTimeout(() => {
    message.value = "信息更新成功！";
    messageType.value = "success";
    submitting.value = false;
    form.password = "";
    form.confirmPassword = "";
  }, 1000);
};

const resetForm = () => {
  form.nickname = "当前用户";
  form.email = "user@example.com";
  form.password = "";
  form.confirmPassword = "";
  avatarPreview.value = null;
  message.value = "";
};
</script>

<style scoped>
.page-container {
  min-height: 100vh;
  padding-top: 70px;
  background: linear-gradient(145deg, #667eea 0%, #764ba2 100%);
  display: flex;
}

.content-area {
  flex: 1;
  margin-left: 240px;
  padding: 2rem;
  transition: margin-left 0.3s ease;
}

.user-sidebar.collapsed ~ .content-area {
  margin-left: 70px;
}

.form-card {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  border-radius: 2rem;
  border: 1px solid rgba(255, 255, 255, 0.2);
  padding: 2.5rem;
  color: white;
  box-shadow: 0 20px 35px -8px rgba(0, 0, 0, 0.2);
  max-width: 600px;
  margin: 0 auto;
}

.page-title {
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  text-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.page-subtitle {
  font-size: 1.1rem;
  margin-bottom: 2rem;
  opacity: 0.9;
}

/* 头像区域 */
.avatar-section {
  display: flex;
  gap: 2rem;
  align-items: center;
  margin-bottom: 2rem;
  background: rgba(255, 255, 255, 0.1);
  padding: 1.5rem;
  border-radius: 1.2rem;
  border: 1px solid rgba(255, 255, 255, 0.15);
}

.avatar-preview {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border: 2px solid white;
}

.avatar-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  font-size: 2rem;
  opacity: 0.7;
}

.avatar-upload {
  flex: 1;
}

.upload-label {
  display: inline-block;
  background: white;
  color: #667eea;
  padding: 0.5rem 1.2rem;
  border-radius: 30px;
  font-weight: 500;
  cursor: pointer;
  transition: transform 0.2s;
  margin-bottom: 0.5rem;
}

.upload-label:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 15px rgba(0, 0, 0, 0.2);
}

.hidden-input {
  display: none;
}

.hint {
  font-size: 0.85rem;
  opacity: 0.7;
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
  opacity: 0.9;
}

.form-group input {
  width: 100%;
  padding: 0.8rem 1.2rem;
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 30px;
  color: white;
  font-size: 1rem;
  transition:
    border-color 0.2s,
    background 0.2s;
}

.form-group input:focus {
  outline: none;
  border-color: white;
  background: rgba(255, 255, 255, 0.25);
}

.form-group input::placeholder {
  color: rgba(255, 255, 255, 0.6);
}

/* 提示信息 */
.form-message {
  padding: 0.8rem 1.2rem;
  border-radius: 30px;
  margin-bottom: 1.5rem;
  text-align: center;
}

.form-message.success {
  background: rgba(34, 197, 94, 0.2);
  border: 1px solid rgba(34, 197, 94, 0.3);
}

.form-message.error {
  background: rgba(239, 68, 68, 0.2);
  border: 1px solid rgba(239, 68, 68, 0.3);
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
  border-radius: 50px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition:
    transform 0.2s,
    box-shadow 0.2s;
  flex: 1;
}

.submit-btn {
  background: white;
  color: #667eea;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 15px rgba(0, 0, 0, 0.2);
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.cancel-btn {
  background: transparent;
  color: white;
  border: 2px solid white;
}

.cancel-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  transform: translateY(-2px);
}

/* 响应式 */
@media (max-width: 768px) {
  .content-area {
    margin-left: 0;
    padding: 1rem;
  }
  .form-card {
    padding: 1.5rem;
  }
  .avatar-section {
    flex-direction: column;
    text-align: center;
  }
}
</style>
