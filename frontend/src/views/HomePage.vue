<template>
  <div class="content home-page layout-page-shell layout-page-shell--wide">
    <div class="hero">
      <div class="hero-content">
        <h1 class="title">智能体安全评测平台</h1>
        <p class="subtitle">安全 · 可靠 · 专业的智能体评估系统</p>
        <p class="description">
          让每一次评测都有据可依，助您打造更安全的智能体
        </p>
      </div>

      <div class="guide-card ui-surface-glass">
        <h2 class="guide-title">快速上手</h2>
        <div class="steps-grid">
          <div
            class="step-item ui-surface-white ui-hover-card"
            v-for="(step, index) in steps"
            :key="index"
          >
            <div class="step-number">{{ index + 1 }}</div>
            <h3>{{ step.title }}</h3>
            <p>{{ step.desc }}</p>
          </div>
        </div>
      </div>

      <div class="actions">
        <div class="primary-actions">
          <button class="btn primary ui-btn ui-btn-pill" @click="goDataset">
            <AppIcon icon="lucide:database" class="btn-icon" />
            <span>浏览评测目录</span>
          </button>
          <button class="btn primary ui-btn ui-btn-pill" @click="goLeaderboard">
            <AppIcon icon="lucide:trophy" class="btn-icon" />
            <span>查看排行榜</span>
          </button>
        </div>

        <div class="user-actions">
          <template v-if="!isLogin">
            <button
              class="btn accent ui-btn ui-btn-pill ui-btn-gradient"
              @click="openLoginDialog"
            >
              <AppIcon icon="lucide:log-in" class="btn-icon" />
              <span>登录 / 注册</span>
            </button>
          </template>
          <template v-else>
            <div class="welcome-card">
              <span class="greeting"
                >欢迎回来，<strong>{{ username }}</strong
                >！</span
              >
              <div class="action-buttons">
                <router-link :to="RouteLocation.userCenter" class="btn outline ui-btn ui-btn-pill">
                  <AppIcon icon="lucide:layout-dashboard" class="btn-icon" />
                  <span>个人中心</span>
                </router-link>
                <button
                  class="btn logout ui-btn ui-btn-pill"
                  @click="handleLogoutClick"
                >
                  <AppIcon icon="lucide:log-out" class="btn-icon" />
                  <span>退出</span>
                </button>
              </div>
            </div>
          </template>
        </div>
      </div>
    </div>
  </div>

  <ConfirmDialog
    v-model="showLogoutConfirm"
    title="确认退出"
    message="您确定要退出登录吗？"
    confirm-text="退出"
    cancel-text="取消"
    :danger="true"
    :loading="logoutLoading"
    @confirm="handleLogoutConfirm"
    @cancel="handleLogoutCancel"
  />
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useUserStore } from "@/store/UserStore";
import { storeToRefs } from "pinia";
import ConfirmDialog from "@/components/dialog/ConfirmDialog.vue";
import AppIcon from "@/components/icon/AppIcon.vue";
import { RouteLocation } from "@/router/RouteNames";

const router = useRouter();
const userStore = useUserStore();
const { isLogin, username } = storeToRefs(userStore);

const steps = [
  { title: "注册/登录", desc: "创建账号或登录，开启评测之旅" },
  { title: "提交智能体", desc: "在个人中心上传您的智能体，选择风险域与评测项" },
  { title: "查看报告", desc: "获取详细评测结果，优化智能体性能" },
  { title: "登上榜单", desc: "公开您的智能体，与其他开发者一较高下" },
];

const goDataset = () => router.push(RouteLocation.datasetList);
const goLeaderboard = () => router.push(RouteLocation.leaderboard);
const openLoginDialog = () => userStore.openLoginDialog();

const showLogoutConfirm = ref(false);
const logoutLoading = ref(false);

const handleLogoutClick = () => {
  showLogoutConfirm.value = true;
};

const handleLogoutConfirm = () => {
  logoutLoading.value = true;
  setTimeout(() => {
    userStore.logout();
    router.push(RouteLocation.home);
    showLogoutConfirm.value = false;
    logoutLoading.value = false;
  }, 100);
};

const handleLogoutCancel = () => {
  showLogoutConfirm.value = false;
};
</script>

<style scoped>
@keyframes float {
  0%,
  100% {
    transform: translateY(0);
  }

  50% {
    transform: translateY(-5px);
  }
}

.home-page {
  min-height: calc(100vh - var(--nav-height));
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  width: 100%;
  padding-bottom: 2.5rem;
}

.hero {
  width: 100%;
  padding: 1rem 0 2rem;
  color: #1e293b;
  position: relative;
  z-index: 2;
}

.hero-content {
  text-align: center;
  margin-bottom: 3rem;
  animation: fadeInUp 1s ease;
}

.title {
  font-size: 3.5rem;
  font-weight: 800;
  margin-bottom: 0.5rem;
}

.subtitle {
  font-size: 1.5rem;
  font-weight: 500;
  margin-bottom: 0.5rem;
  letter-spacing: 1px;
  color: #475569;
}

.description {
  font-size: 1.1rem;
  color: #64748b;
  max-width: 600px;
  margin: 0 auto;
}

.guide-card {
  border-radius: 3rem;
  padding: 2.5rem;
  margin: 3rem 0;
  transition: transform 0.3s ease;
}

.guide-card:hover {
  transform: scale(1.01);
}

.guide-title {
  text-align: center;
  font-size: 2rem;
  margin-bottom: 2rem;
  font-weight: 600;
  color: #0f172a;
}

.steps-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 2rem;
}

.step-item {
  padding: 1.5rem 1rem;
  text-align: center;
  cursor: default;
}

.step-number {
  width: 60px;
  height: 60px;
  background: linear-gradient(135deg, #2563eb, #7c3aed);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.8rem;
  font-weight: 700;
  margin: 0 auto 1rem;
  box-shadow: 0 8px 16px -4px rgba(37, 99, 235, 0.3);
}

.step-item h3 {
  font-size: 1.3rem;
  margin-bottom: 0.5rem;
  color: #0f172a;
}

.step-item p {
  font-size: 0.9rem;
  color: #64748b;
  line-height: 1.5;
}

.actions {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  align-items: center;
  margin-top: 2rem;
}

.primary-actions {
  display: flex;
  gap: 1.2rem;
  flex-wrap: wrap;
  justify-content: center;
}

.user-actions {
  display: flex;
  justify-content: center;
  width: 100%;
}

.welcome-card {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  background: white;
  backdrop-filter: blur(5px);
  padding: 0.8rem 2rem;
  border-radius: 50px;
  box-shadow: 0 5px 20px rgba(0, 0, 0, 0.05);
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.greeting {
  font-size: 1.1rem;
  color: #334155;
}

.greeting strong {
  color: #2563eb;
  font-weight: 600;
}

.action-buttons {
  display: flex;
  gap: 0.8rem;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.6rem;
  padding: 0.9rem 2.2rem;
  border: none;
  font-size: 1rem;
  text-decoration: none;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.02);
}

.btn span {
  display: inline-flex;
  align-items: center;
}

.btn-icon {
  font-size: 1.2rem;
  flex-shrink: 0;
}

.btn:hover {
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 12px 24px -8px rgba(0, 0, 0, 0.15);
}

.btn:active {
  transform: translateY(0);
}

.primary {
  background: white;
  color: #1e293b;
  border: 1px solid #e2e8f0;
}

.primary:hover {
  background: #f8fafc;
  border-color: #cbd5e1;
}

.accent:hover {
  background: linear-gradient(135deg, #1d4ed8, #6d28d9);
}

.outline {
  background: transparent;
  color: #2563eb;
  border: 2px solid #2563eb30;
  padding: 0.6rem 1.5rem;
}

.outline:hover {
  background: #2563eb0c;
  border-color: #2563eb;
}

.logout {
  background: transparent;
  color: #ef4444;
  border: 2px solid #ef444430;
  padding: 0.6rem 1.5rem;
}

.logout:hover {
  background: #ef44440c;
  border-color: #ef4444;
}

@media (max-width: 768px) {
  .title {
    font-size: 2.5rem;
  }

  .subtitle {
    font-size: 1.2rem;
  }

  .steps-grid {
    grid-template-columns: 1fr;
  }

  .primary-actions {
    flex-direction: column;
    width: 100%;
  }

  .primary-actions .btn {
    width: 100%;
    justify-content: center;
  }

  .welcome-card {
    flex-direction: column;
    gap: 1rem;
    padding: 1.2rem;
    border-radius: 30px;
  }

  .action-buttons {
    flex-direction: column;
    width: 100%;
  }

  .action-buttons .btn {
    width: 100%;
    justify-content: center;
  }
}
</style>
