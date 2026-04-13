<template>
  <div class="content home-page layout-page-shell layout-page-shell--wide">
    <section class="hero-grid">
      <section class="hero-main ui-surface-glass ui-glow-frame">
        <div class="brand-lockup">
          <span class="brand-badge ui-surface-white">
            <BrandLogo class="hero-logo" alt="智能体安全评测平台标志" :priority="true" />
          </span>
          <span class="brand-name">Agent Security Evaluation</span>
        </div>

        <h1 class="hero-title ui-title-gradient">智能体安全评测平台</h1>
        <p class="hero-description hero-description--desktop-single-line">
          浏览数据集、提交评测任务、跟踪运行状态，并查看最终结果。
        </p>

        <div class="hero-actions">
          <UiButton :to="RouteLocation.datasetList" variant="primary">
            浏览数据集
          </UiButton>
          <UiButton
            v-if="isLogin"
            :to="RouteLocation.agentSubmit"
            variant="secondary"
          >
            提交评测
          </UiButton>
          <UiButton
            v-else
            variant="secondary"
            @click="openLoginDialog"
          >
            登录 / 注册
          </UiButton>
          <UiButton
            :to="isLogin ? RouteLocation.userCenter : RouteLocation.contact"
            variant="ghost"
          >
            {{ isLogin ? "查看记录" : "联系我们" }}
          </UiButton>
        </div>
      </section>

      <aside class="hero-side ui-surface-white">
        <h2>快速开始</h2>
        <div class="hero-checklist">
          <div class="hero-check">
            <strong>1. 选择数据集</strong>
            <p>按风险域查看数据集说明、样例和资源。</p>
          </div>
          <div class="hero-check">
            <strong>2. 配置接入方式</strong>
            <p>填写 API 或 Docker 信息并确认运行参数。</p>
          </div>
          <div class="hero-check">
            <strong>3. 跟踪评测结果</strong>
            <p>在工作台查看进度、状态和最终报告。</p>
          </div>
        </div>
      </aside>
    </section>

    <section class="home-stats">
      <HomeStatsRow :items="statsItems" />
    </section>

    <section class="workflow-section">
      <div class="section-head">
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
        <UiButton :to="RouteLocation.userCenter" variant="primary">
          评测记录
        </UiButton>
        <UiButton :to="RouteLocation.userProfile" variant="secondary">
          个人资料
        </UiButton>
        <UiButton variant="ghost" @click="handleLogoutClick">
          退出登录
        </UiButton>
      </div>
    </section>

    <InlineNotice
      v-if="catalogError"
      tone="warning"
      title="数据集目录暂不可用"
      :message="catalogError"
    />

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
import { computed, onMounted, ref } from "vue";
import { storeToRefs } from "pinia";
import { useRouter } from "vue-router";
import { useUserStore } from "@/modules/account/stores/UserStore";
import { useDatasetCatalogStore } from "@/modules/dataset/stores/DatasetCatalogStore";
import ConfirmDialog from "@/shared/ui/feedback/ConfirmDialog.vue";
import BrandLogo from "@/shared/ui/branding/BrandLogo.vue";
import InlineNotice from "@/shared/ui/feedback/InlineNotice.vue";
import UiButton from "@/shared/ui/actions/UiButton.vue";
import HomeStatsRow from "@/modules/public/components/HomeStatsRow.vue";
import HomeWorkflowCard from "@/modules/public/components/HomeWorkflowCard.vue";
import { RouteLocation } from "@/app/router/RouteNames";

const router = useRouter();
const userStore = useUserStore();
const datasetCatalogStore = useDatasetCatalogStore();
const { isLogin, username } = storeToRefs(userStore);
const {
  enabledCategories,
  categories,
  error: catalogError,
  loaded,
} = storeToRefs(datasetCatalogStore);

const datasetCount = computed(() =>
  enabledCategories.value.reduce(
    (count, category) => count + category.subcategories.length,
    0,
  ),
);

const statsItems = computed(() => [
  {
    label: "风险域",
    value: loaded.value ? String(enabledCategories.value.length) : "--",
    description: "当前可浏览的风险域数量",
  },
  {
    label: "数据集",
    value: loaded.value ? String(datasetCount.value) : "--",
    description: "支持直接发起评测的数据集数量",
  },
  {
    label: "目录状态",
    value: loaded.value && categories.value.length ? "已同步" : "待加载",
    description: "首页展示基于当前目录能力",
  },
  {
    label: "当前状态",
    value: isLogin.value ? "已登录" : "游客",
    description: isLogin.value ? "可直接进入工作台" : "登录后可创建评测任务",
  },
]);

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

onMounted(async () => {
  if (!loaded.value) {
    await datasetCatalogStore.fetchCatalog();
  }
});
</script>

<style scoped>
.home-page {
  padding-bottom: 2.5rem;
}

.hero-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.45fr) minmax(300px, 0.9fr);
  gap: 1rem;
  align-items: stretch;
}

.hero-main,
.hero-side,
.workspace-card {
  border-radius: 1.6rem;
  padding: 1.2rem;
}

.brand-lockup {
  display: inline-flex;
  align-items: center;
  gap: 0.7rem;
  margin-bottom: 0.95rem;
}

.brand-badge {
  width: 3rem;
  height: 3rem;
  padding: 0.5rem;
  border-radius: 1rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.hero-logo {
  width: 100%;
  height: 100%;
}

.brand-name {
  color: #4338ca;
  font-size: 0.82rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.hero-title {
  margin: 0;
  font-size: clamp(2.5rem, 5.2vw, 4.3rem);
  line-height: 1.02;
  letter-spacing: -0.05em;
}

.hero-description {
  margin: 0.9rem 0 0;
  max-width: none;
  color: var(--color-text-muted);
  font-size: 1rem;
  line-height: 1.75;
}

.hero-description--desktop-single-line {
  white-space: nowrap;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-top: 1.15rem;
}

.hero-side h2,
.section-head h2,
.workspace-copy h2 {
  margin: 0;
}

.hero-checklist {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
  margin-top: 0.9rem;
}

.hero-check strong {
  color: var(--color-text-main);
}

.hero-check p,
.section-head p,
.workspace-copy p {
  margin: 0.38rem 0 0;
  color: var(--color-text-subtle);
  line-height: 1.7;
}

.workflow-section {
  margin-top: 1rem;
}

.home-stats {
  margin-top: 1rem;
}

.home-stats :deep(.metric-value) {
  background: var(--grad-primary);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  text-shadow: 0 12px 28px rgba(79, 70, 229, 0.18);
}

.workflow-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.85rem;
  margin-top: 0.9rem;
}

.workspace-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-top: 1rem;
}

.workspace-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

@media (max-width: 1080px) {
  .hero-grid,
  .workflow-grid {
    grid-template-columns: 1fr 1fr;
  }

  .hero-main {
    grid-column: 1 / -1;
  }
}

@media (max-width: 768px) {
  .hero-grid,
  .workflow-grid {
    grid-template-columns: 1fr;
  }

  .hero-actions,
  .workspace-card,
  .workspace-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .hero-description--desktop-single-line {
    white-space: normal;
  }
}
</style>
