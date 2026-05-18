<template>
  <div class="content home-page layout-page-shell layout-page-shell--wide">
    <section class="hero-stage" aria-labelledby="home-hero-title">
      <div class="hero-shell">
        <BrandLogo
          class="hero-logo"
          :alt="t('common.brand.logoAlt')"
          :priority="true"
        />

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
            leading-icon="app:action.browseDataset"
          >
            {{ t("common.actions.browseDataset") }}
          </UiButton>
          <UiButton
            v-if="isLogin"
            :to="RouteLocation.agentSubmit"
            variant="primary"
            size="lg"
            leading-icon="app:action.submitEvaluation"
          >
            {{ t("common.actions.submitEvaluation") }}
          </UiButton>
          <UiButton
            v-else
            variant="primary"
            size="lg"
            leading-icon="app:action.login"
            @click="openLoginDialog"
          >
            {{ t("common.actions.loginRegister") }}
          </UiButton>
          <UiButton
            :to="isLogin ? RouteLocation.userCenter : RouteLocation.contact"
            variant="primary"
            size="lg"
            :leading-icon="
              isLogin ? 'app:action.viewRecords' : 'app:action.contactUs'
            "
          >
            {{
              isLogin
                ? t("common.actions.viewRecords")
                : t("common.actions.contactUs")
            }}
          </UiButton>
        </div>
      </div>

      <button
        class="section-jump section-jump--hero"
        type="button"
        :aria-label="t('public.home.navigation.aria')"
        :aria-controls="sectionContentId(heroSectionJump.key)"
        @click="scrollToSectionContent(heroSectionJump.key)"
        @mousemove="handleSectionJumpGlow"
        @focus="handleSectionJumpGlow"
      >
        <span class="section-jump__title ui-title-gradient">
          {{ heroSectionJump.title }}
        </span>
        <span class="section-jump__description">
          {{ heroSectionJump.description }}
        </span>
      </button>
    </section>

    <section
      :id="sectionContentId('quickstart')"
      :ref="(element) => setSectionRef('quickstart', element)"
      class="home-section workflow-section"
      :class="{ 'home-section--visible': isSectionVisible('quickstart') }"
      aria-labelledby="home-quickstart-title"
    >
      <div class="section-intro">
        <p class="section-kicker">{{ t("public.home.quickstart.kicker") }}</p>
        <h2 id="home-quickstart-title">
          {{ t("public.home.quickstart.title") }}
        </h2>
        <p>{{ t("public.home.quickstart.description") }}</p>
      </div>
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

    <template
      v-for="{ jump, section } in introSectionsWithJumps"
      :key="section.key"
    >
      <button
        class="section-jump section-jump--between"
        type="button"
        :aria-controls="sectionContentId(jump.key)"
        @click="scrollToSectionContent(jump.key)"
        @mousemove="handleSectionJumpGlow"
        @focus="handleSectionJumpGlow"
      >
        <span class="section-jump__title ui-title-gradient">
          {{ jump.title }}
        </span>
        <span class="section-jump__description">
          {{ jump.description }}
        </span>
      </button>

      <section
        :id="sectionContentId(section.key)"
        :ref="(element) => setSectionRef(section.key, element)"
        class="home-section product-section"
        :class="[
          `home-section--${section.key}`,
          { 'home-section--visible': isSectionVisible(section.key) },
        ]"
        :aria-labelledby="`${sectionContentId(section.key)}-title`"
      >
        <div class="product-section__layout">
          <div class="section-intro product-section__intro">
            <p class="section-kicker">{{ section.kicker }}</p>
            <h2 :id="`${sectionContentId(section.key)}-title`">
              {{ section.title }}
            </h2>
            <p>{{ section.description }}</p>
          </div>

          <div v-if="section.key === 'loop'" class="loop-panel">
            <article
              v-for="(item, index) in section.items"
              :key="item.key"
              class="loop-step"
            >
              <span class="loop-step__index">
                {{ formatSectionStep(index) }}
              </span>
              <span class="loop-step__icon">
                <AppIcon :icon="item.icon" />
              </span>
              <div class="loop-step__copy">
                <h3>{{ item.title }}</h3>
                <p>{{ item.description }}</p>
              </div>
            </article>
          </div>

          <div v-else-if="section.key === 'trust'" class="trust-trace">
            <article
              v-for="item in section.items"
              :key="item.key"
              class="trust-trace__item"
            >
              <span class="trust-trace__icon">
                <AppIcon :icon="item.icon" />
              </span>
              <h3>{{ item.title }}</h3>
              <p>{{ item.description }}</p>
            </article>
          </div>

          <div
            v-else
            class="product-grid"
            :class="`product-grid--${section.key}`"
          >
            <article
              v-for="item in section.items"
              :key="item.key"
              class="product-card"
            >
              <span class="product-card__icon">
                <AppIcon :icon="item.icon" />
              </span>
              <h3>{{ item.title }}</h3>
              <p>{{ item.description }}</p>
              <UiButton
                v-if="item.to && item.actionLabel"
                :to="item.to"
                variant="text"
                size="sm"
              >
                {{ item.actionLabel }}
              </UiButton>
            </article>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import {
  computed,
  nextTick,
  onBeforeUnmount,
  onMounted,
  ref,
  watch,
  type ComponentPublicInstance,
} from "vue";
import type { RouteLocationRaw } from "vue-router";
import { storeToRefs } from "pinia";
import { useI18n } from "vue-i18n";
import { useUserStore } from "@/modules/account/stores/userStore";
import AppIcon from "@/shared/ui/branding/AppIcon.vue";
import BrandLogo from "@/shared/ui/branding/BrandLogo.vue";
import UiButton from "@/shared/ui/actions/UiButton.vue";
import HomeWorkflowStep from "@/modules/public/components/HomeWorkflowStep.vue";
import { RouteLocation } from "@/app/router/route-names";
import type { AppIconName } from "@/shared/ui/branding/app-icon-registry";

const { locale, t } = useI18n();
const userStore = useUserStore();
const { isLogin } = storeToRefs(userStore);

const displayedTitle = ref("");
const displayedDescriptionPrimary = ref("");
const displayedDescriptionSecondary = ref("");
const visibleSections = ref<Set<HomeSectionKey>>(new Set());

const typingHandles: number[] = [];
let prefersReducedMotion = false;
let sectionObserver: IntersectionObserver | null = null;
let observedSectionKeys = new WeakMap<Element, HomeSectionKey>();

const HOME_SECTION_KEYS = [
  "quickstart",
  "capabilities",
  "loop",
  "trust",
  "resources",
] as const;

type HomeSectionKey = (typeof HOME_SECTION_KEYS)[number];

type HomeInfoSectionKey = Exclude<HomeSectionKey, "quickstart">;

const sectionRefs: Partial<Record<HomeSectionKey, HTMLElement>> = {};

const heroTitle = computed(() => t("common.brand.name"));
const heroDescriptionPrimary = computed(() =>
  t("public.home.hero.descriptionPrimary"),
);
const heroDescriptionSecondary = computed(() =>
  t("public.home.hero.descriptionSecondary"),
);

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
  displayedTitle.value = heroTitle.value;
  displayedDescriptionPrimary.value = heroDescriptionPrimary.value;
  displayedDescriptionSecondary.value = heroDescriptionSecondary.value;
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

interface WorkflowItem {
  step: number;
  icon: AppIconName;
  title: string;
  description: string;
  actionLabel: string;
  to: RouteLocationRaw;
}

interface HomeSectionJump {
  key: HomeSectionKey;
  title: string;
  description: string;
}

interface HomeSectionItem {
  key: string;
  icon: AppIconName;
  title: string;
  description: string;
  actionLabel?: string;
  to?: RouteLocationRaw;
}

interface HomeInfoSection {
  key: HomeInfoSectionKey;
  kicker: string;
  title: string;
  description: string;
  items: HomeSectionItem[];
}

interface HomeInfoSectionWithJump {
  jump: HomeSectionJump;
  section: HomeInfoSection;
}

const sectionContentId = (key: HomeSectionKey): string => `home-${key}-content`;

const sectionJumpMap = computed<Record<HomeSectionKey, HomeSectionJump>>(() => ({
  quickstart: {
    key: "quickstart",
    title: t("public.home.quickstart.title"),
    description: t("public.home.navigation.quickstart"),
  },
  capabilities: {
    key: "capabilities",
    title: t("public.home.sections.capabilities.title"),
    description: t("public.home.navigation.capabilities"),
  },
  loop: {
    key: "loop",
    title: t("public.home.sections.loop.title"),
    description: t("public.home.navigation.loop"),
  },
  trust: {
    key: "trust",
    title: t("public.home.sections.trust.title"),
    description: t("public.home.navigation.trust"),
  },
  resources: {
    key: "resources",
    title: t("public.home.sections.resources.title"),
    description: t("public.home.navigation.resources"),
  },
}));

const heroSectionJump = computed<HomeSectionJump>(
  () => sectionJumpMap.value.quickstart,
);

const workflowItems = computed<WorkflowItem[]>(() => [
  {
    step: 1,
    icon: "app:home.workflow.browse",
    title: t("public.home.workflow.browse.title"),
    description: t("public.home.workflow.browse.description"),
    actionLabel: t("public.home.workflow.browse.action"),
    to: RouteLocation.datasetList,
  },
  {
    step: 2,
    icon: "app:home.workflow.submit",
    title: t("public.home.workflow.submit.title"),
    description: t("public.home.workflow.submit.description"),
    actionLabel: isLogin.value
      ? t("public.home.workflow.submit.actionAuthed")
      : t("public.home.workflow.submit.actionGuest"),
    to: isLogin.value ? RouteLocation.agentSubmit : RouteLocation.datasetList,
  },
  {
    step: 3,
    icon: "app:home.workflow.track",
    title: t("public.home.workflow.track.title"),
    description: t("public.home.workflow.track.description"),
    actionLabel: isLogin.value
      ? t("public.home.workflow.track.actionAuthed")
      : t("public.home.workflow.track.actionGuest"),
    to: isLogin.value ? RouteLocation.userCenter : RouteLocation.contact,
  },
  {
    step: 4,
    icon: "app:home.workflow.review",
    title: t("public.home.workflow.review.title"),
    description: t("public.home.workflow.review.description"),
    actionLabel: isLogin.value
      ? t("public.home.workflow.review.actionAuthed")
      : t("public.home.workflow.review.actionGuest"),
    to: isLogin.value ? RouteLocation.userCenter : RouteLocation.contact,
  },
]);

const introSections = computed<HomeInfoSection[]>(() => [
  {
    key: "capabilities",
    kicker: t("public.home.sections.capabilities.kicker"),
    title: t("public.home.sections.capabilities.title"),
    description: t("public.home.sections.capabilities.description"),
    items: [
      {
        key: "datasets",
        icon: "app:home.section.dataset",
        title: t("public.home.sections.capabilities.items.datasets.title"),
        description: t(
          "public.home.sections.capabilities.items.datasets.description",
        ),
      },
      {
        key: "evaluation",
        icon: "app:home.section.evaluation",
        title: t("public.home.sections.capabilities.items.evaluation.title"),
        description: t(
          "public.home.sections.capabilities.items.evaluation.description",
        ),
      },
      {
        key: "report",
        icon: "app:home.section.report",
        title: t("public.home.sections.capabilities.items.report.title"),
        description: t(
          "public.home.sections.capabilities.items.report.description",
        ),
      },
      {
        key: "ranking",
        icon: "app:home.section.ranking",
        title: t("public.home.sections.capabilities.items.ranking.title"),
        description: t(
          "public.home.sections.capabilities.items.ranking.description",
        ),
      },
    ],
  },
  {
    key: "loop",
    kicker: t("public.home.sections.loop.kicker"),
    title: t("public.home.sections.loop.title"),
    description: t("public.home.sections.loop.description"),
    items: [
      {
        key: "scope",
        icon: "app:home.section.scope",
        title: t("public.home.sections.loop.items.scope.title"),
        description: t("public.home.sections.loop.items.scope.description"),
      },
      {
        key: "submit",
        icon: "app:home.section.submit",
        title: t("public.home.sections.loop.items.submit.title"),
        description: t("public.home.sections.loop.items.submit.description"),
      },
      {
        key: "evidence",
        icon: "app:home.section.evidence",
        title: t("public.home.sections.loop.items.evidence.title"),
        description: t("public.home.sections.loop.items.evidence.description"),
      },
    ],
  },
  {
    key: "trust",
    kicker: t("public.home.sections.trust.kicker"),
    title: t("public.home.sections.trust.title"),
    description: t("public.home.sections.trust.description"),
    items: [
      {
        key: "standard",
        icon: "app:home.section.standard",
        title: t("public.home.sections.trust.items.standard.title"),
        description: t("public.home.sections.trust.items.standard.description"),
      },
      {
        key: "privacy",
        icon: "app:home.section.privacy",
        title: t("public.home.sections.trust.items.privacy.title"),
        description: t("public.home.sections.trust.items.privacy.description"),
      },
      {
        key: "confidence",
        icon: "app:home.section.confidence",
        title: t("public.home.sections.trust.items.confidence.title"),
        description: t("public.home.sections.trust.items.confidence.description"),
      },
    ],
  },
  {
    key: "resources",
    kicker: t("public.home.sections.resources.kicker"),
    title: t("public.home.sections.resources.title"),
    description: t("public.home.sections.resources.description"),
    items: [
      {
        key: "catalog",
        icon: "app:home.section.dataset",
        title: t("public.home.sections.resources.items.catalog.title"),
        description: t("public.home.sections.resources.items.catalog.description"),
        actionLabel: t("common.actions.browseDataset"),
        to: RouteLocation.datasetList,
      },
      {
        key: "submit",
        icon: "app:home.section.submit",
        title: t("public.home.sections.resources.items.submit.title"),
        description: t("public.home.sections.resources.items.submit.description"),
        actionLabel: isLogin.value
          ? t("common.actions.submitEvaluation")
          : t("public.home.workflow.submit.actionGuest"),
        to: isLogin.value ? RouteLocation.agentSubmit : RouteLocation.datasetList,
      },
      {
        key: "leaderboard",
        icon: "app:home.section.ranking",
        title: t("public.home.sections.resources.items.leaderboard.title"),
        description: t(
          "public.home.sections.resources.items.leaderboard.description",
        ),
        actionLabel: t("layout.nav.leaderboard"),
        to: RouteLocation.leaderboard,
      },
      {
        key: "contact",
        icon: "app:home.section.contact",
        title: t("public.home.sections.resources.items.contact.title"),
        description: t("public.home.sections.resources.items.contact.description"),
        actionLabel: t("common.actions.contactUs"),
        to: RouteLocation.contact,
      },
    ],
  },
]);

const introSectionsWithJumps = computed<HomeInfoSectionWithJump[]>(() =>
  introSections.value.map((section) => ({
    jump: sectionJumpMap.value[section.key],
    section,
  })),
);

const openLoginDialog = () => {
  userStore.openLoginDialog();
};

const setSectionRef = (
  key: HomeSectionKey,
  element: Element | ComponentPublicInstance | null,
) => {
  if (element instanceof HTMLElement) {
    sectionRefs[key] = element;
  } else {
    delete sectionRefs[key];
  }
};

const isSectionVisible = (key: HomeSectionKey): boolean =>
  visibleSections.value.has(key);

const markSectionVisible = (key: HomeSectionKey) => {
  visibleSections.value = new Set([...visibleSections.value, key]);
};

const scrollToSectionContent = (key: HomeSectionKey) => {
  sectionRefs[key]?.scrollIntoView({
    behavior: prefersReducedMotion ? "auto" : "smooth",
    block: "start",
  });
};

const handleSectionJumpGlow = (event: MouseEvent | FocusEvent) => {
  const target = event.currentTarget as HTMLElement | null;

  if (!target) {
    return;
  }

  const rect = target.getBoundingClientRect();
  const x =
    event instanceof MouseEvent ? event.clientX - rect.left : rect.width / 2;
  const y =
    event instanceof MouseEvent ? event.clientY - rect.top : rect.height / 2;

  target.style.setProperty("--jump-x", `${x}px`);
  target.style.setProperty("--jump-y", `${y}px`);
};

const formatSectionStep = (index: number): string =>
  String(index + 1).padStart(2, "0");

const observeSections = async () => {
  await nextTick();

  sectionObserver?.disconnect();
  sectionObserver = null;

  if (prefersReducedMotion) {
    visibleSections.value = new Set(HOME_SECTION_KEYS);
    return;
  }

  observedSectionKeys = new WeakMap<Element, HomeSectionKey>();
  sectionObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!(entry.target instanceof HTMLElement) || !entry.isIntersecting) {
          return;
        }

        const key = observedSectionKeys.get(entry.target);
        if (key) {
          markSectionVisible(key);
        }
      });
    },
    {
      threshold: 0.18,
    },
  );

  HOME_SECTION_KEYS.forEach((key) => {
    const element = sectionRefs[key];
    if (!element) {
      return;
    }

    observedSectionKeys.set(element, key);
    sectionObserver?.observe(element);
  });
};

const startHeroAnimation = () => {
  clearTypingHandles();
  displayedTitle.value = "";
  displayedDescriptionPrimary.value = "";
  displayedDescriptionSecondary.value = "";
  visibleSections.value = prefersReducedMotion
    ? new Set(HOME_SECTION_KEYS)
    : new Set();

  if (prefersReducedMotion) {
    setHeroImmediately();
  } else {
    const titleEndDelay = typeText(heroTitle.value, displayedTitle, 220, 118);
    const primaryEndDelay = typeText(
      heroDescriptionPrimary.value,
      displayedDescriptionPrimary,
      titleEndDelay + 320,
      46,
    );
    typeText(
      heroDescriptionSecondary.value,
      displayedDescriptionSecondary,
      primaryEndDelay + 160,
      42,
    );
  }
};

onMounted(() => {
  prefersReducedMotion = window.matchMedia(
    "(prefers-reduced-motion: reduce)",
  ).matches;

  startHeroAnimation();
  void observeSections();
});

watch(locale, () => {
  startHeroAnimation();
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
  min-width: 0;
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
  min-width: 0;
  text-align: center;
}

.hero-logo {
  width: 5rem;
  flex-shrink: 0;
  filter: drop-shadow(0 12px 28px rgba(79, 70, 229, 0.14));
}

.hero-title {
  margin: 0;
  min-height: 1.22em;
  padding-block: 0.08em 0.12em;
  font-size: clamp(3rem, 8vw, 5.25rem);
  line-height: 1.02;
  letter-spacing: 0;
  text-wrap: balance;
  overflow-wrap: anywhere;
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
  font-size: 1.08rem;
  font-weight: 500;
  line-height: 1.68;
  text-align: center;
  overflow-wrap: anywhere;
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
  min-width: 0;
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

.section-jump {
  --jump-x: 50%;
  --jump-y: 50%;
  position: relative;
  z-index: 1;
  display: flex;
  width: min(54rem, 100%);
  min-width: 0;
  flex-direction: column;
  align-items: center;
  gap: 0.68rem;
  margin-inline: auto;
  padding: 1.5rem 1rem 1.35rem;
  border: 0;
  border-top: 1px solid rgba(148, 163, 184, 0.2);
  background: transparent;
  color: inherit;
  cursor: pointer;
  font: inherit;
  text-align: center;
  transition:
    border-color var(--duration-fast) var(--ease-standard),
    transform var(--duration-fast) var(--ease-standard);
}

.section-jump--hero {
  margin-top: clamp(2.4rem, 5vw, 3.8rem);
}

.section-jump--between {
  margin-top: clamp(3.2rem, 7vw, 6rem);
}

.section-jump::before {
  content: "";
  position: absolute;
  inset: 0;
  background:
    radial-gradient(
      360px circle at var(--jump-x) var(--jump-y),
      rgba(59, 130, 246, 0.12),
      rgba(139, 92, 246, 0.06) 48%,
      transparent 72%
    ),
    linear-gradient(180deg, rgba(255, 255, 255, 0.56), transparent);
  opacity: 0.72;
  transition: opacity var(--duration-fast) var(--ease-standard);
  pointer-events: none;
}

.section-jump:hover,
.section-jump:focus-visible {
  border-color: rgba(37, 99, 235, 0.34);
  transform: translateY(-1px);
}

.section-jump:hover::before,
.section-jump:focus-visible::before {
  opacity: 1;
}

.section-jump:focus-visible {
  outline: none;
  box-shadow: var(--shadow-focus-primary);
}

.section-jump__title,
.section-jump__description {
  position: relative;
  z-index: 1;
}

.section-jump__title {
  font-size: clamp(1.9rem, 4vw, 2.75rem);
  font-weight: 850;
  letter-spacing: 0;
  line-height: 1.16;
  overflow-wrap: anywhere;
}

.section-jump__description {
  max-width: 46rem;
  color: rgba(71, 85, 105, 0.92);
  font-size: 1rem;
  line-height: 1.7;
  overflow-wrap: anywhere;
}

.home-section {
  min-width: 0;
  scroll-margin-top: calc(var(--nav-height) + 1.25rem);
  margin-top: clamp(1.5rem, 3vw, 2.4rem);
  opacity: 0;
  transform: translate3d(0, 18px, 0);
  transition:
    opacity var(--duration-base) var(--ease-standard),
    transform var(--duration-base) var(--ease-emphasized);
}

.home-section--visible {
  opacity: 1;
  transform: translate3d(0, 0, 0);
}

.section-intro {
  display: flex;
  max-width: 50rem;
  min-width: 0;
  flex-direction: column;
  gap: 0.55rem;
  margin-bottom: 1.15rem;
}

.section-kicker {
  margin: 0;
  color: var(--color-primary);
  font-size: 0.78rem;
  font-weight: 850;
}

.section-intro h2 {
  margin: 0;
  color: var(--color-text-dark);
  font-size: clamp(1.65rem, 3.2vw, 2.35rem);
  line-height: 1.18;
  letter-spacing: 0;
  overflow-wrap: anywhere;
}

.section-intro p:last-child {
  margin: 0;
  color: var(--color-text-subtle);
  font-size: 1rem;
  line-height: 1.72;
  overflow-wrap: anywhere;
}

.workflow-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 1.05rem;
  min-width: 0;
}

.product-section {
  padding-block: clamp(0.8rem, 2vw, 1.4rem);
}

.product-section__layout {
  display: grid;
  grid-template-columns: minmax(0, 0.78fr) minmax(0, 1.22fr);
  align-items: start;
  gap: clamp(1.6rem, 4vw, 3rem);
  min-width: 0;
}

.product-section__intro {
  margin-bottom: 0;
}

.product-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
  min-width: 0;
}

.product-grid--resources {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.product-card {
  position: relative;
  display: flex;
  min-width: 0;
  min-height: 13.5rem;
  flex-direction: column;
  gap: 0.75rem;
  padding: 1.15rem;
  overflow: hidden;
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: var(--radius-control-sm);
  background:
    linear-gradient(rgba(37, 99, 235, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(37, 99, 235, 0.05) 1px, transparent 1px),
    rgba(255, 255, 255, 0.68);
  background-size: 4.8rem 4.8rem;
  box-shadow: var(--shadow-surface-soft);
  transition:
    border-color var(--duration-fast) var(--ease-standard),
    box-shadow var(--duration-fast) var(--ease-standard),
    transform var(--duration-fast) var(--ease-standard);
}

.product-card:hover {
  border-color: rgba(37, 99, 235, 0.28);
  box-shadow: var(--shadow-surface-hover);
  transform: translateY(-1px);
}

.product-card__icon {
  display: inline-flex;
  width: 2.35rem;
  height: 2.35rem;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(37, 99, 235, 0.16);
  border-radius: var(--radius-control-sm);
  background: rgba(219, 234, 254, 0.5);
  color: var(--color-primary);
}

.home-section--resources .product-card__icon {
  border-color: rgba(217, 119, 6, 0.2);
  background: rgba(254, 243, 199, 0.58);
  color: #b45309;
}

.product-card h3 {
  margin: 0;
  color: var(--color-text-dark);
  font-size: 1.04rem;
  line-height: 1.42;
  overflow-wrap: anywhere;
}

.product-card p {
  margin: 0;
  flex: 1;
  color: var(--color-text-muted);
  line-height: 1.7;
  overflow-wrap: anywhere;
}

.product-card :deep(.ui-button) {
  align-self: flex-start;
}

.loop-panel {
  display: grid;
  min-width: 0;
  overflow: hidden;
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: var(--radius-control-sm);
  background:
    linear-gradient(135deg, rgba(15, 23, 42, 0.98), rgba(30, 41, 59, 0.96)),
    var(--color-text-dark);
  box-shadow: var(--shadow-panel-elevated);
}

.loop-step {
  display: grid;
  grid-template-columns: auto auto minmax(0, 1fr);
  align-items: start;
  gap: 0.9rem;
  min-width: 0;
  padding: 1.15rem;
  border-top: 1px solid rgba(148, 163, 184, 0.18);
}

.loop-step:first-child {
  border-top: 0;
}

.loop-step__index {
  color: rgba(203, 213, 225, 0.62);
  font-family: var(
    --font-mono,
    ui-monospace,
    SFMono-Regular,
    Menlo,
    Monaco,
    Consolas,
    monospace
  );
  font-size: 0.84rem;
  font-weight: 800;
  line-height: 2.35rem;
}

.loop-step__icon {
  display: inline-flex;
  width: 2.35rem;
  height: 2.35rem;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(96, 165, 250, 0.26);
  border-radius: var(--radius-control-sm);
  background: rgba(59, 130, 246, 0.12);
  color: #93c5fd;
}

.loop-step__copy {
  min-width: 0;
}

.loop-step__copy h3,
.trust-trace__item h3 {
  margin: 0;
  font-size: 1.04rem;
  line-height: 1.42;
  overflow-wrap: anywhere;
}

.loop-step__copy h3 {
  color: rgba(248, 250, 252, 0.94);
}

.loop-step__copy p,
.trust-trace__item p {
  margin: 0.45rem 0 0;
  line-height: 1.7;
  overflow-wrap: anywhere;
}

.loop-step__copy p {
  color: rgba(203, 213, 225, 0.74);
}

.trust-trace {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1rem;
  min-width: 0;
}

.trust-trace__item {
  position: relative;
  min-width: 0;
  padding: 1.1rem 1rem;
  border-top: 1px solid rgba(5, 150, 105, 0.2);
}

.trust-trace__item::before {
  content: "";
  position: absolute;
  top: -1px;
  left: 0;
  width: 3rem;
  height: 1px;
  background: linear-gradient(90deg, rgba(5, 150, 105, 0.8), transparent);
}

.trust-trace__icon {
  display: inline-flex;
  width: 2.35rem;
  height: 2.35rem;
  align-items: center;
  justify-content: center;
  margin-bottom: 0.85rem;
  border: 1px solid rgba(5, 150, 105, 0.18);
  border-radius: var(--radius-control-sm);
  background: rgba(209, 250, 229, 0.52);
  color: #047857;
}

.trust-trace__item h3 {
  color: var(--color-text-dark);
}

.trust-trace__item p {
  color: var(--color-text-muted);
}

@media (max-width: 1080px) {
  .workflow-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .product-section__layout {
    grid-template-columns: 1fr;
  }

  .product-grid,
  .trust-trace {
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
    font-size: 3rem;
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

  .section-jump {
    width: 100%;
    margin-top: 1.8rem;
    padding-inline: 0.35rem;
  }

  .section-jump--between {
    margin-top: 3.2rem;
  }

  .product-grid,
  .workflow-grid,
  .trust-trace {
    grid-template-columns: 1fr;
  }

  .loop-step {
    grid-template-columns: auto minmax(0, 1fr);
  }

  .loop-step__index {
    grid-row: span 2;
  }

  .loop-step__icon {
    display: none;
  }

  .product-card {
    min-height: auto;
  }
}

@media (max-width: 420px) {
  .hero-title {
    font-size: 2.55rem;
  }

  .hero-description {
    max-width: 100%;
  }

  .section-jump__title {
    font-size: 2rem;
  }
}
</style>
