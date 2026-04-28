<template>
  <div class="content home-page layout-page-shell layout-page-shell--wide">
    <section class="hero-stage" aria-labelledby="home-hero-title">
      <div class="hero-shell">
        <BrandLogo class="hero-logo" alt="智能体安全评测平台标志" :priority="true" />

        <h1 id="home-hero-title" class="hero-title ui-title-gradient">
          {{ displayedTitle }}
        </h1>

        <p class="hero-description">
          <span>{{ displayedDescriptionPrimary }}</span>
          <span>{{ displayedDescriptionSecondary }}</span>
        </p>

        <div class="hero-actions">
          <UiButton
            :to="RouteLocation.datasetList"
            variant="primary"
            size="lg"
            leading-icon="lucide:database"
          >
            浏览数据集
          </UiButton>
          <UiButton
            v-if="isLogin"
            :to="RouteLocation.agentSubmit"
            variant="primary"
            size="lg"
            leading-icon="lucide:file-plus-2"
          >
            提交评测
          </UiButton>
          <UiButton
            v-else
            variant="primary"
            size="lg"
            leading-icon="lucide:log-in"
            @click="openLoginDialog"
          >
            登录 / 注册
          </UiButton>
          <UiButton
            :to="isLogin ? RouteLocation.userCenter : RouteLocation.contact"
            variant="primary"
            size="lg"
            :leading-icon="isLogin ? 'lucide:clipboard-list' : 'lucide:messages-square'"
          >
            {{ isLogin ? "查看记录" : "联系我们" }}
          </UiButton>
        </div>
      </div>

      <button
        class="hero-anchor"
        type="button"
        aria-controls="home-quickstart"
        @click="scrollToQuickstart"
        @mousemove="handleQuickstartGlow"
        @focus="handleQuickstartGlow"
      >
        <span class="hero-anchor__title ui-title-gradient">快速上手</span>
        <span class="hero-anchor__description">
          以标准化流程完成数据集浏览、评测提交、执行跟踪与结果复核。
        </span>
      </button>
    </section>

    <section
      id="home-quickstart"
      ref="quickstartSection"
      class="workflow-section"
      :class="{ 'workflow-section--visible': workflowVisible }"
    >
      <div class="workflow-grid">
        <HomeWorkflowStep
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
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from "vue";
import { storeToRefs } from "pinia";
import { useUserStore } from "@/modules/account/stores/userStore";
import BrandLogo from "@/shared/ui/branding/BrandLogo.vue";
import UiButton from "@/shared/ui/actions/UiButton.vue";
import HomeWorkflowStep from "@/modules/public/components/HomeWorkflowStep.vue";
import { RouteLocation } from "@/app/router/route-names";

const HERO_TITLE = "AEGIS 智能体安全评测平台";
const HERO_DESCRIPTION_PRIMARY =
  "Agents Evaluation and Guardrail Inspection System";
const HERO_DESCRIPTION_SECONDARY =
  "安全、可靠、专业的智能体评估系统，让每一次评测都有据可依";

const userStore = useUserStore();
const { isLogin } = storeToRefs(userStore);

const displayedTitle = ref("");
const displayedDescriptionPrimary = ref("");
const displayedDescriptionSecondary = ref("");
const quickstartSection = ref<HTMLElement | null>(null);
const workflowVisible = ref(false);

const typingHandles: number[] = [];
let prefersReducedMotion = false;
let sectionObserver: IntersectionObserver | null = null;

const scheduleTyping = (callback: () => void, delay: number) => {
  const handle = window.setTimeout(callback, delay);
  typingHandles.push(handle);
};

const clearTypingHandles = () => {
  typingHandles.forEach((handle) => {
    window.clearTimeout(handle);
  });
  typingHandles.length = 0;
};

const setHeroImmediately = () => {
  displayedTitle.value = HERO_TITLE;
  displayedDescriptionPrimary.value = HERO_DESCRIPTION_PRIMARY;
  displayedDescriptionSecondary.value = HERO_DESCRIPTION_SECONDARY;
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

const openLoginDialog = () => {
  userStore.openLoginDialog();
};

const scrollToQuickstart = () => {
  quickstartSection.value?.scrollIntoView({
    behavior: prefersReducedMotion ? "auto" : "smooth",
    block: "start",
  });
};

const handleQuickstartGlow = (event: MouseEvent | FocusEvent) => {
  const target = event.currentTarget as HTMLElement | null;

  if (!target) {
    return;
  }

  const rect = target.getBoundingClientRect();
  const x = event instanceof MouseEvent ? event.clientX - rect.left : rect.width / 2;
  const y = event instanceof MouseEvent ? event.clientY - rect.top : rect.height / 2;

  target.style.setProperty("--anchor-x", `${x}px`);
  target.style.setProperty("--anchor-y", `${y}px`);
};

const observeSections = async () => {
  await nextTick();

  sectionObserver?.disconnect();
  sectionObserver = null;

  if (prefersReducedMotion) {
    workflowVisible.value = true;
    return;
  }

  sectionObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!(entry.target instanceof HTMLElement) || !entry.isIntersecting) {
          return;
        }

        workflowVisible.value = true;
      });
    },
    {
      threshold: 0.18,
    },
  );

  if (quickstartSection.value) {
    sectionObserver.observe(quickstartSection.value);
  }
};

onMounted(() => {
  prefersReducedMotion = window.matchMedia(
    "(prefers-reduced-motion: reduce)",
  ).matches;

  displayedTitle.value = "";
  displayedDescriptionPrimary.value = "";
  displayedDescriptionSecondary.value = "";
  workflowVisible.value = prefersReducedMotion;

  if (prefersReducedMotion) {
    setHeroImmediately();
  } else {
    const titleEndDelay = typeText(HERO_TITLE, displayedTitle, 220, 118);
    const primaryEndDelay = typeText(
      HERO_DESCRIPTION_PRIMARY,
      displayedDescriptionPrimary,
      titleEndDelay + 320,
      46,
    );
    typeText(
      HERO_DESCRIPTION_SECONDARY,
      displayedDescriptionSecondary,
      primaryEndDelay + 160,
      42,
    );
  }

  void observeSections();
});

onBeforeUnmount(() => {
  clearTypingHandles();
  sectionObserver?.disconnect();
});
</script>

<style scoped lang="scss">
.home-page {
  padding-bottom: 2.8rem;
}

.hero-stage {
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: calc(100vh - var(--nav-height) - 1rem);
  padding: clamp(2.4rem, 6vw, 4.2rem) 0 1.6rem;
  isolation: isolate;
}

.hero-shell {
  position: relative;
  z-index: 1;
  display: flex;
  flex: 1;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1.15rem;
  text-align: center;
}

.hero-logo {
  width: clamp(4.15rem, 7.4vw, 5.4rem);
  flex-shrink: 0;
  filter: drop-shadow(0 12px 28px rgba(79, 70, 229, 0.14));
}

.hero-title {
  margin: 0;
  min-height: 1.22em;
  padding-block: 0.08em 0.12em;
  font-size: clamp(3.45rem, 7.3vw, 6.3rem);
  line-height: 1.02;
  letter-spacing: -0.075em;
  text-wrap: balance;
}

.hero-title.ui-title-gradient {
  text-shadow: 0 10px 24px rgba(99, 102, 241, 0.12);
}

.hero-description {
  display: flex;
  flex-direction: column;
  gap: 0.18rem;
  min-height: 3.74em;
  margin: 0 auto;
  max-width: min(72ch, 760px);
  color: rgba(71, 85, 105, 0.96);
  font-size: clamp(1.02rem, 1.35vw, 1.12rem);
  font-weight: 500;
  line-height: 1.68;
  text-align: center;
}

.hero-description span {
  display: block;
  min-height: 1.68em;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0.95rem;
  margin-top: 0.35rem;
}

.hero-actions :deep(.ui-button) {
  min-width: 166px;
  min-height: 3.5rem;
}

.hero-actions :deep(.ui-button--primary) {
  padding-inline: 1.5rem;
  border-color: rgba(255, 255, 255, 0.2);
  background: linear-gradient(135deg, #2e6fff 0%, #3d6af3 54%, #5a4cf4 100%);
  box-shadow: 0 22px 40px -24px rgba(59, 103, 245, 0.52);
}

.hero-actions :deep(.ui-button--primary:hover:not(.ui-button--disabled)) {
  box-shadow:
    0 26px 46px -24px rgba(59, 103, 245, 0.56),
    0 0 0 1px rgba(255, 255, 255, 0.2) inset;
}

.hero-actions :deep(.ui-button__content) {
  white-space: nowrap;
}

.hero-anchor {
  --anchor-x: 50%;
  --anchor-y: 50%;
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.62rem;
  width: min(50rem, 100%);
  margin: clamp(2.1rem, 4vw, 3rem) auto 0;
  padding: 1.6rem 1rem 0.95rem;
  border: 0;
  border-top: 1px solid rgba(148, 163, 184, 0.2);
  background: transparent;
  cursor: pointer;
  text-align: center;
}

.hero-anchor::before {
  content: "";
  position: absolute;
  inset: 0;
  background: radial-gradient(
    240px circle at var(--anchor-x) var(--anchor-y),
    rgba(99, 102, 241, 0.1),
    transparent 60%
  );
  opacity: 0.62;
  transition:
    background var(--duration-fast) var(--ease-standard),
    opacity var(--duration-fast) var(--ease-standard);
  pointer-events: none;
}

.hero-anchor:hover::before,
.hero-anchor:focus-visible::before {
  background: radial-gradient(
    260px circle at var(--anchor-x) var(--anchor-y),
    rgba(59, 130, 246, 0.14),
    rgba(139, 92, 246, 0.05) 55%,
    transparent 72%
  );
}

.hero-anchor__title,
.hero-anchor__description {
  position: relative;
  z-index: 1;
}

.hero-anchor__title {
  font-size: clamp(1.8rem, 3.5vw, 2.9rem);
  font-weight: 800;
  letter-spacing: -0.05em;
}

.hero-anchor__description {
  max-width: 42rem;
  color: rgba(100, 116, 139, 0.96);
  font-size: 0.98rem;
  line-height: 1.75;
}

.workflow-section {
  margin-top: 0.85rem;
  opacity: 0;
  transform: translate3d(0, 18px, 0);
  transition:
    opacity var(--duration-base) var(--ease-standard),
    transform var(--duration-base) var(--ease-emphasized);
}

.workflow-section--visible {
  opacity: 1;
  transform: translate3d(0, 0, 0);
}

.workflow-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 1.05rem;
}

@media (max-width: 1080px) {
  .workflow-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .hero-description {
    max-width: min(64ch, 100%);
  }
}

@media (max-width: 768px) {
  .hero-stage {
    min-height: auto;
    padding-top: 2.25rem;
  }

  .hero-title {
    min-height: 1.18em;
    font-size: clamp(2.7rem, 14vw, 4.2rem);
  }

  .hero-description {
    max-width: 34ch;
    min-height: 4.8em;
    line-height: 1.58;
  }

  .hero-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .hero-actions :deep(.ui-button) {
    width: 100%;
  }

  .hero-anchor {
    width: 100%;
    margin-top: 1.8rem;
    padding-top: 1.35rem;
  }

  .workflow-grid {
    grid-template-columns: 1fr;
  }
}
</style>
