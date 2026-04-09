<template>
  <div class="content home-page layout-page-shell layout-page-shell--wide">
    <div class="hero">
      <div class="hero-content">
        <div class="hero-brand ui-surface-white">
          <BrandLogo
            class="hero-logo"
            alt="智能体安全评测平台标志"
            :priority="true"
          />
        </div>

        <div class="hero-copy">
          <h1 class="title">
            <span>{{ typedPrimaryText }}</span>
            <span v-if="isPrimaryTyping" class="type-cursor" aria-hidden="true"></span>
          </h1>
          <p class="subtitle">
            <span>{{ typedSecondaryText }}</span>
            <span
              v-if="!isPrimaryTyping && isSecondaryTyping"
              class="type-cursor type-cursor--subtle"
              aria-hidden="true"
            ></span>
          </p>
          <p class="description">
            让每一次评测都有据可依，助您打造更安全、更可靠的智能体。
          </p>
        </div>
      </div>

      <div class="guide-card ui-surface-glass">
        <h2 class="guide-title">快速上手</h2>
        <div class="steps-grid">
          <div
            v-for="(step, index) in steps"
            :key="step.title"
            class="step-item ui-surface-white ui-hover-card"
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
              <span class="greeting">
                欢迎回来，<strong>{{ username }}</strong>
              </span>
              <div class="action-buttons">
                <router-link
                  :to="RouteLocation.userCenter"
                  class="btn outline ui-btn ui-btn-pill"
                >
                  <AppIcon icon="lucide:layout-dashboard" class="btn-icon" />
                  <span>个人中心</span>
                </router-link>
                <button class="btn logout ui-btn ui-btn-pill" @click="handleLogoutClick">
                  <AppIcon icon="lucide:log-out" class="btn-icon" />
                  <span>退出登录</span>
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
    title="确认退出登录"
    message="您确定要退出当前账号吗？"
    confirm-text="退出登录"
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
import { storeToRefs } from "pinia";
import { useUserStore } from "@/modules/account/stores/UserStore";
import { useTypewriterText } from "@/modules/public/composables/useTypewriterText";
import ConfirmDialog from "@/shared/ui/ConfirmDialog.vue";
import AppIcon from "@/shared/ui/AppIcon.vue";
import BrandLogo from "@/shared/ui/BrandLogo.vue";
import { RouteLocation } from "@/app/router/RouteNames";

const PRIMARY_TEXT = "智能体安全评测平台";
const SECONDARY_TEXT = "安全 · 可靠 · 专业的智能体评估系统";

const router = useRouter();
const userStore = useUserStore();
const { isLogin, username } = storeToRefs(userStore);

const { typedPrimaryText, typedSecondaryText, isPrimaryTyping, isSecondaryTyping } =
  useTypewriterText({
    sessionKey: "home-hero-typewriter-v1",
    primaryText: PRIMARY_TEXT,
    secondaryText: SECONDARY_TEXT,
  });

const steps = [
  {
    title: "注册 / 登录",
    desc: "创建账号或登录平台，开启您的评测流程。",
  },
  {
    title: "提交智能体",
    desc: "在个人中心提交智能体，并选择需要覆盖的评测项。",
  },
  {
    title: "查看报告",
    desc: "获取详细评测结果，快速定位风险与改进方向。",
  },
  {
    title: "登上榜单",
    desc: "公开优秀结果，与其他开发者对比整体表现。",
  },
];

const goDataset = () => {
  void router.push(RouteLocation.datasetList);
};

const goLeaderboard = () => {
  void router.push(RouteLocation.leaderboard);
};

const openLoginDialog = () => {
  userStore.openLoginDialog();
};

const showLogoutConfirm = ref(false);
const logoutLoading = ref(false);

const handleLogoutClick = () => {
  showLogoutConfirm.value = true;
};

const handleLogoutConfirm = () => {
  logoutLoading.value = true;
  setTimeout(() => {
    userStore.logout();
    void router.push(RouteLocation.home);
    showLogoutConfirm.value = false;
    logoutLoading.value = false;
  }, 100);
};

const handleLogoutCancel = () => {
  showLogoutConfirm.value = false;
};
</script>

<style scoped>
@keyframes cursorBlink {
  0%,
  48% {
    opacity: 1;
  }

  52%,
  100% {
    opacity: 0;
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
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.25rem;
  text-align: center;
  margin: 0 auto 3rem;
  animation: fadeInUp 1s ease;
}

.hero-brand {
  width: fit-content;
  padding: 1rem 1.2rem;
  border-radius: 1.8rem;
  box-shadow: 0 24px 50px -38px rgba(37, 99, 235, 0.45);
}

.hero-logo {
  width: clamp(6.5rem, 14vw, 10.5rem);
}

.hero-copy {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  max-width: 760px;
}

.title,
.subtitle {
  display: inline-flex;
  align-items: baseline;
  justify-content: center;
  gap: 0.18em;
  margin: 0;
  text-wrap: balance;
}

.title {
  min-height: 2.35em;
  font-size: clamp(2.5rem, 5vw, 4.25rem);
  font-weight: 800;
  letter-spacing: -0.04em;
  line-height: 1.05;
  background: linear-gradient(135deg, #0f172a, #2563eb 68%, #7c3aed);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.subtitle {
  min-height: 3em;
  font-size: clamp(1.15rem, 2vw, 1.55rem);
  font-weight: 600;
  letter-spacing: 0.08em;
  color: #475569;
}

.description {
  margin: 0;
  font-size: 1.08rem;
  color: #64748b;
  max-width: 42rem;
  line-height: 1.75;
}

.type-cursor {
  display: inline-block;
  width: 0.12em;
  min-width: 0.12em;
  height: 0.95em;
  border-radius: 999px;
  background: currentColor;
  animation: cursorBlink 1s steps(1) infinite;
  transform: translateY(0.06em);
}

.type-cursor--subtle {
  opacity: 0.82;
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
  margin: 0 0 2rem;
  font-weight: 600;
  color: #0f172a;
}

.steps-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
  gap: 1.4rem;
}

.step-item {
  padding: 1.5rem 1.1rem;
  text-align: center;
  cursor: default;
}

.step-number {
  width: 60px;
  height: 60px;
  background: linear-gradient(135deg, #2563eb, #7c3aed);
  color: #ffffff;
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
  font-size: 1.2rem;
  margin: 0 0 0.5rem;
  color: #0f172a;
}

.step-item p {
  margin: 0;
  font-size: 0.95rem;
  color: #64748b;
  line-height: 1.6;
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
  background: #ffffff;
  backdrop-filter: blur(5px);
  padding: 0.8rem 2rem;
  border-radius: 999px;
  box-shadow: 0 5px 20px rgba(0, 0, 0, 0.05);
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.greeting {
  font-size: 1.05rem;
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
  background: #ffffff;
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

@media (max-width: 1024px) {
  .home-page {
    align-items: flex-start;
  }

  .hero {
    padding-top: 0.25rem;
  }

  .guide-card {
    border-radius: 2.2rem;
    padding: 2rem 1.6rem;
  }
}

@media (max-width: 768px) {
  .hero-content {
    gap: 1rem;
    margin-bottom: 2.25rem;
  }

  .title {
    min-height: 2.75em;
  }

  .subtitle {
    min-height: 3.8em;
  }

  .description {
    font-size: 1rem;
  }

  .steps-grid {
    grid-template-columns: 1fr;
  }

  .primary-actions {
    flex-direction: column;
    width: 100%;
  }

  .primary-actions .btn,
  .user-actions > .btn {
    width: 100%;
    justify-content: center;
  }

  .welcome-card {
    flex-direction: column;
    gap: 1rem;
    width: 100%;
    padding: 1.2rem;
    border-radius: 2rem;
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

@media (max-width: 480px) {
  .hero-brand {
    padding: 0.85rem 1rem;
    border-radius: 1.4rem;
  }

  .guide-card {
    padding: 1.5rem 1.1rem;
    border-radius: 1.8rem;
  }

  .guide-title {
    font-size: 1.55rem;
  }

  .step-item {
    padding: 1.25rem 0.95rem;
  }
}
</style>