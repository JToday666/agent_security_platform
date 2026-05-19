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

      <HomeSectionJump
        :id="sectionJumpId(quickstartJump.key)"
        variant="hero"
        :title="quickstartJump.title"
        :description="quickstartJump.description"
        :controls="sectionContentId(quickstartJump.key)"
        :jump-aria-label="
          t('public.home.navigation.jumpAria', { section: quickstartJump.title })
        "
        @activate="scrollToSectionJump(quickstartJump.key)"
      />
    </section>

    <section
      :id="sectionContentId('quickstart')"
      :ref="(element) => setSectionRef('quickstart', element)"
      class="home-section workflow-section"
      :class="{ 'home-section--visible': isSectionVisible('quickstart') }"
      :aria-label="quickstartJump.title"
    >
      <h2 class="visually-hidden">{{ quickstartJump.title }}</h2>
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
      <HomeSectionJump
        :id="sectionJumpId(jump.key)"
        :title="jump.title"
        :description="jump.description"
        :controls="sectionContentId(jump.key)"
        :jump-aria-label="
          t('public.home.navigation.jumpAria', { section: jump.title })
        "
        @activate="scrollToSectionJump(jump.key)"
      />

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
        <h2
          :id="`${sectionContentId(section.key)}-title`"
          class="visually-hidden"
        >
          {{ jump.title }}
        </h2>

        <div v-if="section.kind === 'aegis'" class="aegis-statement">
          <span class="aegis-statement__eyebrow">
            {{ t("public.home.sections.aegis.nameLabel") }}
          </span>
          <strong class="aegis-statement__title">AEGIS</strong>
          <p class="aegis-statement__expansion">{{ section.expansion }}</p>
          <p class="aegis-statement__lead">{{ section.description }}</p>
          <div class="aegis-statement__story-grid">
            <p
              v-for="storyLine in section.story"
              :key="storyLine"
              class="aegis-statement__story"
            >
              {{ storyLine }}
            </p>
          </div>
        </div>

        <div v-else class="product-section__layout">
          <div class="section-context">
            <p>{{ section.description }}</p>
          </div>

          <div v-if="section.kind === 'loop'" class="loop-panel">
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

          <div v-else-if="section.kind === 'trust'" class="trust-layout">
            <div class="trust-trace">
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

            <aside
              class="leaderboard-preview"
              :aria-label="t('public.home.sections.trust.leaderboard.aria')"
            >
              <div class="leaderboard-preview__head">
                <div>
                  <span>{{ t("public.home.sections.trust.leaderboard.kicker") }}</span>
                  <h3>{{ t("public.home.sections.trust.leaderboard.title") }}</h3>
                </div>
                <UiButton :to="RouteLocation.leaderboard" variant="text" size="sm">
                  {{ t("layout.nav.leaderboard") }}
                </UiButton>
              </div>

              <div v-if="leaderboardLoading" class="leaderboard-preview__state">
                {{ t("common.feedback.pleaseWait") }}
              </div>
              <div
                v-else-if="leaderboardUnavailable"
                class="leaderboard-preview__state"
              >
                {{ t("public.home.sections.trust.leaderboard.unavailable") }}
              </div>
              <div
                v-else-if="leaderboardPreviewEntries.length"
                class="leaderboard-preview__list"
              >
                <article
                  v-for="entry in leaderboardPreviewEntries"
                  :key="`${entry.rankNo}-${entry.displayName}`"
                  class="leaderboard-preview__row"
                >
                  <span class="leaderboard-preview__rank">
                    {{
                      t("public.home.sections.trust.leaderboard.rank", {
                        rank: entry.rankNo,
                      })
                    }}
                  </span>
                  <span class="leaderboard-preview__name">
                    {{ entry.displayName }}
                  </span>
                  <span class="leaderboard-preview__score">
                    {{ formatScore(entry.officialConservativeScore) }}
                  </span>
                  <span class="leaderboard-preview__meta">
                    {{
                      t("public.home.sections.trust.leaderboard.meta", {
                        risk: formatScore(entry.unsafeRiskScore),
                        confidence: formatScore(entry.confidence),
                      })
                    }}
                  </span>
                </article>
              </div>
              <div v-else class="leaderboard-preview__state">
                {{ t("public.home.sections.trust.leaderboard.empty") }}
              </div>
            </aside>
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
import { RouteLocation } from "@/app/router/route-names";
import { useUserStore } from "@/modules/account/stores/userStore";
import { getLeaderboardSnapshot } from "@/modules/leaderboard/api/leaderboard-api";
import type { LeaderboardEntry } from "@/modules/leaderboard/types/leaderboard-types";
import HomeSectionJump from "@/modules/public/components/HomeSectionJump.vue";
import HomeWorkflowStep from "@/modules/public/components/HomeWorkflowStep.vue";
import UiButton from "@/shared/ui/actions/UiButton.vue";
import AppIcon from "@/shared/ui/branding/AppIcon.vue";
import type { AppIconName } from "@/shared/ui/branding/app-icon-registry";
import BrandLogo from "@/shared/ui/branding/BrandLogo.vue";

const { locale, t } = useI18n();
const userStore = useUserStore();
const { isLogin } = storeToRefs(userStore);

const displayedTitle = ref("");
const displayedDescriptionPrimary = ref("");
const displayedDescriptionSecondary = ref("");
const visibleSections = ref<Set<HomeSectionKey>>(new Set());
const leaderboardEntries = ref<LeaderboardEntry[]>([]);
const leaderboardLoading = ref(false);
const leaderboardUnavailable = ref(false);

const typingHandles: number[] = [];
let prefersReducedMotion = false;
let sectionObserver: IntersectionObserver | null = null;
let observedSectionKeys = new WeakMap<Element, HomeSectionKey>();

const HOME_SECTION_KEYS = [
  "quickstart",
  "capabilities",
  "loop",
  "trust",
  "aegis",
  "experience",
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

const sectionContentId = (key: HomeSectionKey): string => `home-${key}-content`;
const sectionJumpId = (key: HomeSectionKey): string => `home-${key}-jump`;

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

interface HomeSectionJumpConfig {
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
  kind: "cards" | "loop" | "trust" | "aegis" | "experience";
  description: string;
  items: HomeSectionItem[];
  expansion?: string;
  story?: string[];
}

interface HomeInfoSectionWithJump {
  jump: HomeSectionJumpConfig;
  section: HomeInfoSection;
}

const sectionJumpMap = computed<Record<HomeSectionKey, HomeSectionJumpConfig>>(
  () => ({
    quickstart: {
      key: "quickstart",
      title: t("public.home.quickstart.title"),
      description: t("public.home.quickstart.description"),
    },
    capabilities: {
      key: "capabilities",
      title: t("public.home.sections.capabilities.kicker"),
      description: t("public.home.sections.capabilities.title"),
    },
    loop: {
      key: "loop",
      title: t("public.home.sections.loop.kicker"),
      description: t("public.home.sections.loop.title"),
    },
    trust: {
      key: "trust",
      title: t("public.home.sections.trust.kicker"),
      description: t("public.home.sections.trust.title"),
    },
    aegis: {
      key: "aegis",
      title: t("public.home.sections.aegis.kicker"),
      description: t("public.home.sections.aegis.title"),
    },
    experience: {
      key: "experience",
      title: t("public.home.sections.experience.kicker"),
      description: t("public.home.sections.experience.title"),
    },
  }),
);

const quickstartJump = computed<HomeSectionJumpConfig>(
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
    kind: "cards",
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
    kind: "loop",
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
    kind: "trust",
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
    key: "aegis",
    kind: "aegis",
    description: t("public.home.sections.aegis.description"),
    expansion: t("public.home.sections.aegis.expansion"),
    story: [
      t("public.home.sections.aegis.story.guardian"),
      t("public.home.sections.aegis.story.platform"),
    ],
    items: [],
  },
  {
    key: "experience",
    kind: "experience",
    description: t("public.home.sections.experience.description"),
    items: [
      {
        key: "catalog",
        icon: "app:home.section.dataset",
        title: t("public.home.sections.experience.items.catalog.title"),
        description: t("public.home.sections.experience.items.catalog.description"),
        actionLabel: t("common.actions.browseDataset"),
        to: RouteLocation.datasetList,
      },
      {
        key: "submit",
        icon: "app:home.section.submit",
        title: t("public.home.sections.experience.items.submit.title"),
        description: t("public.home.sections.experience.items.submit.description"),
        actionLabel: isLogin.value
          ? t("common.actions.submitEvaluation")
          : t("public.home.workflow.submit.actionGuest"),
        to: isLogin.value ? RouteLocation.agentSubmit : RouteLocation.datasetList,
      },
      {
        key: "leaderboard",
        icon: "app:home.section.ranking",
        title: t("public.home.sections.experience.items.leaderboard.title"),
        description: t(
          "public.home.sections.experience.items.leaderboard.description",
        ),
        actionLabel: t("layout.nav.leaderboard"),
        to: RouteLocation.leaderboard,
      },
      {
        key: "contact",
        icon: "app:home.section.contact",
        title: t("public.home.sections.experience.items.contact.title"),
        description: t("public.home.sections.experience.items.contact.description"),
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

const leaderboardPreviewEntries = computed(() =>
  leaderboardEntries.value.slice(0, 3),
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

const scrollToSectionJump = (key: HomeSectionKey) => {
  document.getElementById(sectionJumpId(key))?.scrollIntoView({
    behavior: prefersReducedMotion ? "auto" : "smooth",
    block: "start",
  });
};

const formatSectionStep = (index: number): string =>
  String(index + 1).padStart(2, "0");

const formatScore = (score: number): string => score.toFixed(1);

const loadLeaderboardPreview = async () => {
  leaderboardLoading.value = true;
  leaderboardUnavailable.value = false;

  try {
    const snapshot = await getLeaderboardSnapshot();
    leaderboardEntries.value = snapshot.entries;
  } catch {
    leaderboardEntries.value = [];
    leaderboardUnavailable.value = true;
  } finally {
    leaderboardLoading.value = false;
  }
};

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
  void loadLeaderboardPreview();
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
  padding-bottom: 2.2rem;
}

.hero-stage {
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-width: 0;
  min-height: calc(100dvh - var(--nav-height) - 1rem);
  padding: 3.6rem 0 1.5rem;
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
  font-size: 5.25rem;
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
  max-width: min(72ch, 760px);
  margin: 0 auto;
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
  white-space: normal;
}

.home-section {
  display: flex;
  min-width: 0;
  flex-direction: column;
  justify-content: center;
  scroll-margin-top: calc(var(--nav-height) + 1rem);
  margin-top: 1.15rem;
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

.workflow-section {
  padding-block: 1.55rem 1.9rem;
}

.workflow-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 1rem;
  min-width: 0;
}

.product-section {
  padding-block: 2rem;
}

.product-section__layout {
  display: grid;
  grid-template-columns: minmax(0, 0.82fr) minmax(0, 1.18fr);
  align-items: center;
  gap: 1.75rem;
  min-width: 0;
}

.section-context {
  min-width: 0;
  max-width: 34rem;
}

.section-context p {
  margin: 0;
  color: var(--color-text-muted);
  font-size: 1.04rem;
  line-height: 1.72;
  overflow-wrap: anywhere;
}

.product-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
  min-width: 0;
}

.product-card {
  position: relative;
  display: flex;
  min-width: 0;
  min-height: 12.4rem;
  flex-direction: column;
  gap: 0.75rem;
  padding: 1.15rem;
  overflow: hidden;
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: var(--radius-control-sm);
  background: rgba(255, 255, 255, 0.76);
  box-shadow: var(--shadow-surface-soft);
  transition:
    border-color var(--duration-fast) var(--ease-standard),
    box-shadow var(--duration-fast) var(--ease-standard),
    transform var(--duration-fast) var(--ease-standard);
}

.product-card::before {
  content: "";
  position: absolute;
  inset: 0 auto 0 0;
  width: 3px;
  background: linear-gradient(
    180deg,
    rgba(37, 99, 235, 0.66),
    rgba(14, 165, 233, 0.26)
  );
}

.product-card:hover {
  border-color: rgba(37, 99, 235, 0.28);
  box-shadow: var(--shadow-surface-hover);
  transform: translateY(-1px);
}

.product-card__icon,
.loop-step__icon,
.trust-trace__icon {
  display: inline-flex;
  width: 2.35rem;
  height: 2.35rem;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(37, 99, 235, 0.16);
  border-radius: var(--radius-control-sm);
  background: rgba(219, 234, 254, 0.5);
  color: var(--color-primary);
}

.home-section--experience .product-card__icon {
  border-color: rgba(14, 165, 233, 0.22);
  background: rgba(207, 250, 254, 0.58);
  color: #0e7490;
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
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.82), rgba(239, 246, 255, 0.72));
  box-shadow: var(--shadow-surface-mid);
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
  color: rgba(37, 99, 235, 0.68);
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
  border-color: rgba(14, 165, 233, 0.22);
  background: rgba(207, 250, 254, 0.46);
  color: #0369a1;
}

.loop-step__copy {
  min-width: 0;
}

.loop-step__copy h3,
.trust-trace__item h3 {
  margin: 0;
  color: var(--color-text-dark);
  font-size: 1.04rem;
  line-height: 1.42;
  overflow-wrap: anywhere;
}

.loop-step__copy p,
.trust-trace__item p {
  margin: 0.45rem 0 0;
  color: var(--color-text-muted);
  line-height: 1.7;
  overflow-wrap: anywhere;
}

.trust-layout {
  display: grid;
  grid-template-columns: minmax(0, 0.92fr) minmax(280px, 0.78fr);
  gap: 1rem;
  min-width: 0;
}

.trust-trace {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.85rem;
  min-width: 0;
}

.trust-trace__item {
  position: relative;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 0.75rem 0.9rem;
  min-width: 0;
  padding: 1rem;
  border: 1px solid rgba(5, 150, 105, 0.16);
  border-radius: var(--radius-control-sm);
  background: rgba(255, 255, 255, 0.74);
}

.trust-trace__item h3 {
  align-self: center;
}

.trust-trace__item p {
  grid-column: 2;
}

.trust-trace__icon {
  border-color: rgba(5, 150, 105, 0.18);
  background: rgba(209, 250, 229, 0.52);
  color: #047857;
}

.leaderboard-preview {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 0.85rem;
  padding: 1rem;
  border: 1px solid rgba(37, 99, 235, 0.16);
  border-radius: var(--radius-control-sm);
  background: rgba(255, 255, 255, 0.78);
  box-shadow: var(--shadow-surface-soft);
}

.leaderboard-preview__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
  min-width: 0;
}

.leaderboard-preview__head div {
  min-width: 0;
}

.leaderboard-preview__head span {
  display: block;
  color: var(--color-primary);
  font-size: 0.78rem;
  font-weight: 800;
  overflow-wrap: anywhere;
}

.leaderboard-preview__head h3 {
  margin: 0.2rem 0 0;
  color: var(--color-text-dark);
  font-size: 1.1rem;
  line-height: 1.34;
  overflow-wrap: anywhere;
}

.leaderboard-preview__list {
  display: grid;
  gap: 0.65rem;
  min-width: 0;
}

.leaderboard-preview__row {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 0.35rem 0.7rem;
  min-width: 0;
  padding: 0.78rem;
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: var(--radius-control-sm);
  background: rgba(248, 250, 252, 0.76);
}

.leaderboard-preview__rank {
  color: var(--color-primary);
  font-size: 0.78rem;
  font-weight: 850;
}

.leaderboard-preview__name {
  min-width: 0;
  color: var(--color-text-dark);
  font-weight: 760;
  overflow-wrap: anywhere;
}

.leaderboard-preview__score {
  color: #047857;
  font-weight: 850;
  font-variant-numeric: tabular-nums;
}

.leaderboard-preview__meta {
  grid-column: 2 / 4;
  color: var(--color-text-subtle);
  font-size: 0.84rem;
  line-height: 1.55;
  overflow-wrap: anywhere;
}

.leaderboard-preview__state {
  min-width: 0;
  padding: 1rem;
  border: 1px dashed rgba(148, 163, 184, 0.24);
  border-radius: var(--radius-control-sm);
  color: var(--color-text-subtle);
  line-height: 1.7;
  overflow-wrap: anywhere;
}

.aegis-statement {
  position: relative;
  display: flex;
  min-width: 0;
  max-width: 66rem;
  flex-direction: column;
  align-items: center;
  gap: 0.72rem;
  margin-inline: auto;
  padding: 0.6rem 0 0.35rem;
  isolation: isolate;
  text-align: center;
}

.aegis-statement::before {
  content: "";
  position: absolute;
  inset: -1.3rem 8% auto;
  z-index: -1;
  height: 13rem;
  background: radial-gradient(
    50% 66% at 50% 10%,
    rgba(37, 99, 235, 0.13),
    rgba(14, 165, 233, 0.06) 48%,
    transparent 76%
  );
  pointer-events: none;
}

.aegis-statement__eyebrow {
  color: var(--color-primary);
  font-size: 0.86rem;
  font-weight: 850;
  line-height: 1.35;
  overflow-wrap: anywhere;
}

.aegis-statement__title {
  max-width: 100%;
  color: var(--color-text-dark);
  font-size: 5rem;
  font-weight: 880;
  line-height: 0.98;
  letter-spacing: 0;
  overflow-wrap: anywhere;
}

.aegis-statement__expansion {
  max-width: min(58rem, 100%);
  margin: 0;
  color: rgba(51, 65, 85, 0.92);
  font-size: 1.18rem;
  font-weight: 720;
  line-height: 1.55;
  overflow-wrap: anywhere;
}

.aegis-statement__lead {
  max-width: min(62rem, 100%);
  margin: 0.12rem 0 0;
  color: var(--color-text-dark);
  font-size: 1.12rem;
  font-weight: 740;
  line-height: 1.68;
  overflow-wrap: anywhere;
}

.aegis-statement__story-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1.1rem;
  width: min(58rem, 100%);
  min-width: 0;
  margin-top: 0.5rem;
}

.aegis-statement__story {
  min-width: 0;
  margin: 0;
  color: var(--color-text-muted);
  font-size: 1.02rem;
  line-height: 1.78;
  overflow-wrap: anywhere;
}

.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

@media (max-width: 1080px) {
  .workflow-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .product-section__layout {
    grid-template-columns: 1fr;
  }

  .section-context {
    max-width: 58rem;
  }

  .trust-layout {
    grid-template-columns: 1fr;
  }

  .hero-description {
    max-width: min(64ch, 100%);
  }

  .aegis-statement__title {
    font-size: 4rem;
  }
}

@media (max-width: 768px) {
  .home-page {
    padding-bottom: 2rem;
  }

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

  .home-section,
  .workflow-section {
    min-height: auto;
    margin-top: 0.85rem;
  }

  .workflow-section {
    padding-block: 1.3rem 1.45rem;
  }

  .product-section {
    padding-block: 1.35rem;
  }

  .product-section__layout {
    gap: 1rem;
  }

  .product-grid,
  .workflow-grid {
    grid-template-columns: 1fr;
  }

  .section-context p {
    font-size: 1rem;
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

  .trust-trace__item {
    grid-template-columns: 1fr;
  }

  .trust-trace__item p {
    grid-column: auto;
  }

  .leaderboard-preview__head,
  .leaderboard-preview__row {
    grid-template-columns: 1fr;
  }

  .leaderboard-preview__head {
    flex-direction: column;
  }

  .leaderboard-preview__score,
  .leaderboard-preview__meta {
    grid-column: auto;
  }

  .product-card {
    min-height: auto;
  }

  .aegis-statement {
    gap: 0.58rem;
    padding-top: 0.3rem;
  }

  .aegis-statement::before {
    inset-inline: 0;
    height: 10rem;
  }

  .aegis-statement__title {
    font-size: 3rem;
  }

  .aegis-statement__expansion {
    max-width: 34rem;
    font-size: 1.02rem;
    line-height: 1.58;
  }

  .aegis-statement__lead {
    max-width: 36rem;
    font-size: 1.02rem;
    line-height: 1.68;
  }

  .aegis-statement__story-grid {
    grid-template-columns: 1fr;
    gap: 0.7rem;
    width: min(36rem, 100%);
    margin-top: 0.35rem;
  }

  .aegis-statement__story {
    font-size: 0.98rem;
    line-height: 1.72;
  }
}

@media (max-width: 420px) {
  .hero-title {
    font-size: 2.55rem;
  }

  .hero-description {
    max-width: 100%;
  }

  .aegis-statement__title {
    font-size: 2.6rem;
  }
}
</style>
