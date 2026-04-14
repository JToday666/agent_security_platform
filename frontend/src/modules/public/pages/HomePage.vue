<template>
  <div class="content home-page layout-page-shell layout-page-shell--wide">
    <section class="hero-stage" aria-labelledby="home-hero-title">
      <div class="hero-grid-lines" aria-hidden="true"></div>
      <div class="hero-glow hero-glow--left" aria-hidden="true"></div>
      <div class="hero-glow hero-glow--right" aria-hidden="true"></div>
      <div class="hero-orb hero-orb--left" aria-hidden="true"></div>
      <div class="hero-orb hero-orb--right" aria-hidden="true"></div>
      <div class="hero-orb hero-orb--bottom" aria-hidden="true"></div>

      <div class="hero-shell">
        <BrandLogo class="hero-logo" alt="智能体安全评测平台标志" :priority="true" />

        <h1 id="home-hero-title" class="hero-title ui-title-gradient">
          {{ displayedTitle }}
        </h1>

        <p class="hero-description">
          {{ displayedDescription }}
        </p>

        <div class="hero-actions">
          <UiButton :to="RouteLocation.datasetList" variant="primary" size="lg">
            浏览数据集
          </UiButton>
          <UiButton
            v-if="isLogin"
            :to="RouteLocation.agentSubmit"
            variant="primary"
            size="lg"
          >
            提交评测
          </UiButton>
          <UiButton
            v-else
            variant="primary"
            size="lg"
            class="hero-login-button"
            @click="openLoginDialog"
          >
            登录 / 注册
          </UiButton>
          <UiButton
            :to="isLogin ? RouteLocation.userCenter : RouteLocation.contact"
            variant="primary"
            size="lg"
            :class="{ 'hero-contact-button': !isLogin }"
          >
            {{ isLogin ? "查看记录" : "联系我们" }}
          </UiButton>
        </div>
      </div>
    </section>

    <section class="workflow-section">
      <div class="section-head section-head--centered">
        <h2>评测流程</h2>
        <p>按顺序完成浏览、提交、跟踪和查看结果。</p>
      </div>

      <div class="workflow-grid">
        <HomeWorkflowCard
          v-for="item in workflowItems"
          :key="item.step"
          :step="item.step"
          :icon="item.icon"
          :title="item.title"
          :description="item.description"
          :action-label="item.actionLabel"
          :to="item.to"
        />
      </div>
    </section>

    <section v-if="isLogin" class="workspace-card ui-surface-panel">
      <div class="workspace-copy">
        <h2>{{ welcomeTitle }}</h2>
        <p>继续管理评测任务，或更新个人资料。</p>
      </div>

      <div class="workspace-actions">
        <UiButton :to="RouteLocation.userCenter" variant="secondary">
          评测记录
        </UiButton>
        <UiButton :to="RouteLocation.userProfile" variant="secondary">
          个人资料
        </UiButton>
        <UiButton variant="danger" @click="handleLogoutClick">
          退出登录
        </UiButton>
      </div>
    </section>

    <ConfirmDialog
      v-model="showLogoutConfirm"
      title="确认退出登录"
      message="确定退出当前账号吗？"
      confirm-text="退出登录"
      cancel-text="取消"
      :danger="true"
      :loading="logoutLoading"
      @confirm="handleLogoutConfirm"
      @cancel="handleLogoutCancel"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { storeToRefs } from "pinia";
import { useRouter } from "vue-router";
import { useUserStore } from "@/modules/account/stores/userStore";
import ConfirmDialog from "@/shared/ui/feedback/ConfirmDialog.vue";
import BrandLogo from "@/shared/ui/branding/BrandLogo.vue";
import UiButton from "@/shared/ui/actions/UiButton.vue";
import HomeWorkflowCard from "@/modules/public/components/HomeWorkflowCard.vue";
import { RouteLocation } from "@/app/router/route-names";

const HERO_TITLE = "智能体安全评测平台";
const HERO_DESCRIPTION =
  "安全·可靠·专业 的智能体评估系统，让每一次评测都有据可依";

const router = useRouter();
const userStore = useUserStore();
const { isLogin, username } = storeToRefs(userStore);

const displayedTitle = ref("");
const displayedDescription = ref("");
const typingHandles: number[] = [];

const scheduleTyping = (callback: () => void, delay: number) => {
  const handle = window.setTimeout(callback, delay);
  typingHandles.push(handle);
};

const typeText = (
  source: string,
  target: { value: string },
  startDelay: number,
  stepDelay: number,
) => {
  for (let index = 1; index <= source.length; index += 1) {
    scheduleTyping(() => {
      target.value = source.slice(0, index);
    }, startDelay + index * stepDelay);
  }

  return startDelay + source.length * stepDelay;
};

const workflowItems = computed(() => [
  {
    step: 1,
    icon: "lucide:database",
    title: "浏览数据集",
    description: "按风险域查看数据集说明、样例和资源。",
    actionLabel: "查看目录",
    to: RouteLocation.datasetList,
  },
  {
    step: 2,
    icon: "lucide:file-plus-2",
    title: "创建评测任务",
    description: "填写智能体信息并选择本次评测范围。",
    actionLabel: isLogin.value ? "开始提交" : "先浏览数据集",
    to: isLogin.value ? RouteLocation.agentSubmit : RouteLocation.datasetList,
  },
  {
    step: 3,
    icon: "lucide:clipboard-list",
    title: "跟踪任务进度",
    description: "在工作台查看运行状态、暂停和终止结果。",
    actionLabel: isLogin.value ? "查看记录" : "联系我们",
    to: isLogin.value ? RouteLocation.userCenter : RouteLocation.contact,
  },
  {
    step: 4,
    icon: "lucide:file-search",
    title: "查看结果",
    description: "进入详情页查看摘要、告警和详细指标。",
    actionLabel: isLogin.value ? "进入工作台" : "查看联系信息",
    to: isLogin.value ? RouteLocation.userCenter : RouteLocation.contact,
  },
]);

const welcomeTitle = computed(() => {
  const normalized = username.value.trim();
  return normalized ? `欢迎回来，${normalized}` : "欢迎回到工作台";
});

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

onMounted(() => {
  displayedTitle.value = "";
  displayedDescription.value = "";

  const titleEndDelay = typeText(HERO_TITLE, displayedTitle, 240, 126);
  typeText(HERO_DESCRIPTION, displayedDescription, titleEndDelay + 360, 52);
});

onBeforeUnmount(() => {
  typingHandles.forEach((handle) => {
    window.clearTimeout(handle);
  });
  typingHandles.length = 0;
});
</script>

<style scoped lang="scss">
.home-page {
  padding-bottom: 2.8rem;
}

.hero-stage {
  position: relative;
  overflow: hidden;
  isolation: isolate;
  padding: clamp(3.2rem, 7vw, 5.2rem) 0 1.8rem;
}

.hero-grid-lines,
.hero-glow,
.hero-orb {
  pointer-events: none;
  position: absolute;
}

.hero-grid-lines {
  inset: 0;
  background:
    linear-gradient(rgba(99, 102, 241, 0.045) 1px, transparent 1px),
    linear-gradient(90deg, rgba(99, 102, 241, 0.045) 1px, transparent 1px);
  background-size: 88px 88px;
  mask-image: linear-gradient(180deg, rgba(255, 255, 255, 0.82), transparent 92%);
  opacity: 0.62;
}

.hero-glow {
  border-radius: 50%;
  filter: blur(54px);
  opacity: 0.78;
  z-index: -2;
}

.hero-glow--left {
  top: 8%;
  left: 8%;
  width: 320px;
  height: 320px;
  background: radial-gradient(circle, rgba(59, 130, 246, 0.2), transparent 72%);
}

.hero-glow--right {
  right: 8%;
  top: 16%;
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, rgba(168, 85, 247, 0.16), transparent 72%);
}

.hero-shell {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  min-height: clamp(340px, 58vh, 520px);
  text-align: center;
}

.hero-logo {
  width: clamp(4rem, 7vw, 5rem);
  flex-shrink: 0;
}

.hero-title {
  margin: 0;
  min-height: 1.1em;
  font-size: clamp(3.2rem, 7vw, 5.8rem);
  line-height: 0.95;
  letter-spacing: -0.075em;
  text-wrap: balance;
}

.hero-description {
  min-height: 1.8em;
  margin: 0;
  max-width: none;
  color: var(--color-text-muted);
  font-size: clamp(1rem, 1.45vw, 1.12rem);
  line-height: 1.8;
  white-space: nowrap;
}


.hero-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0.85rem;
  margin-top: 0.4rem;
}

.hero-actions :deep(.ui-button) {
  min-width: 140px;
}

.hero-login-button {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.96), rgba(129, 140, 248, 0.96));
  box-shadow: 0 16px 28px -20px rgba(99, 102, 241, 0.56);
}

.hero-login-button:hover:not(.ui-button--disabled) {
  box-shadow: 0 18px 32px -20px rgba(99, 102, 241, 0.62);
}

.hero-contact-button {
  box-shadow: var(--shadow-primary-btn);
}

.workflow-section {
  margin-top: 0.85rem;
}

.section-head {
  margin-bottom: 1rem;
}

.section-head--centered {
  text-align: center;
}

.section-head h2,
.workspace-copy h2 {
  margin: 0;
}

.section-head p,
.workspace-copy p {
  margin: 0.42rem 0 0;
  color: var(--color-text-subtle);
  line-height: 1.72;
}

.workflow-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.95rem;
}

.workspace-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-top: 1.1rem;
  border-radius: 1.45rem;
  padding: 1.18rem 1.24rem;
}

.workspace-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 0.75rem;
}

.hero-orb {
  border-radius: 999px;
  filter: blur(0.2px);
}

.hero-orb::before {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.28),
    rgba(99, 102, 241, 0.12)
  );
}

.hero-orb::after {
  content: "";
  position: absolute;
  inset: -6px;
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: inherit;
}

.hero-orb--left {
  top: 8%;
  left: -2%;
  width: 108px;
  height: 108px;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.16), rgba(255, 255, 255, 0.14));
}

.hero-orb--right {
  right: 2%;
  top: 6%;
  width: 72px;
  height: 72px;
  background: linear-gradient(135deg, rgba(168, 85, 247, 0.16), rgba(255, 255, 255, 0.18));
}

.hero-orb--bottom {
  right: 14%;
  bottom: 4%;
  width: 96px;
  height: 96px;
  background: linear-gradient(135deg, rgba(14, 165, 233, 0.16), rgba(255, 255, 255, 0.16));
}

@media (max-width: 1080px) {
  .workflow-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .hero-description {
    white-space: normal;
  }
}

@media (max-width: 768px) {
  .hero-stage {
    padding-top: 2.7rem;
  }

  .hero-shell {
    min-height: auto;
    gap: 0.9rem;
  }

  .hero-title {
    font-size: clamp(2.5rem, 14vw, 4rem);
  }

  .hero-description {
    max-width: 34ch;
    white-space: normal;
  }

  .hero-actions,
  .workspace-card,
  .workspace-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .workflow-grid {
    grid-template-columns: 1fr;
  }
}
</style>
