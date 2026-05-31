<template>
  <div class="content home-page layout-page-shell layout-page-shell--wide">
    <HomeHeroSection
      :displayed-title="displayedTitle"
      :displayed-description-primary="displayedDescriptionPrimary"
      :displayed-description-secondary="displayedDescriptionSecondary"
      :is-login="isLogin"
      :quickstart-jump="quickstartJump"
      :quickstart-content-id="sectionContentId(quickstartJump.key)"
      :quickstart-jump-id="sectionJumpId(quickstartJump.key)"
      :quickstart-jump-aria-label="
        t('public.home.navigation.jumpAria', { section: quickstartJump.title })
      "
      @login="openLoginDialog"
      @jump="scrollToSectionContent(quickstartJump.key)"
    />

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
        @activate="scrollToSectionContent(jump.key)"
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

        <HomeSectionContent
          :section="section"
          :leaderboard-entries="leaderboardPreviewEntries"
          :leaderboard-loading="leaderboardLoading"
          :leaderboard-unavailable="leaderboardUnavailable"
        />
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
import { storeToRefs } from "pinia";
import { useI18n } from "vue-i18n";
import { useUserStore } from "@/modules/account/stores/userStore";
import { getLeaderboardSnapshot } from "@/modules/leaderboard/api/leaderboard-api";
import type { LeaderboardEntry } from "@/modules/leaderboard/types/leaderboard-types";
import HomeHeroSection from "@/modules/public/components/HomeHeroSection.vue";
import HomeSectionContent from "@/modules/public/components/HomeSectionContent.vue";
import HomeSectionJump from "@/modules/public/components/HomeSectionJump.vue";
import HomeWorkflowStep from "@/modules/public/components/HomeWorkflowStep.vue";
import {
  buildIntroSections,
  buildSectionJumpMap,
  buildWorkflowItems,
  HOME_SECTION_KEYS,
} from "@/modules/public/model/home-page-content";
import { resolveHomeSectionScrollTop } from "@/modules/public/model/home-page-scroll";
import type {
  HomeInfoSection,
  HomeInfoSectionWithJump,
  HomeSectionJumpConfig,
  HomeSectionKey,
} from "@/modules/public/model/home-page-types";

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

const sectionJumpMap = computed<Record<HomeSectionKey, HomeSectionJumpConfig>>(
  () => buildSectionJumpMap(t),
);

const quickstartJump = computed<HomeSectionJumpConfig>(
  () => sectionJumpMap.value.quickstart,
);

const workflowItems = computed(() => buildWorkflowItems(t, isLogin.value));

const introSections = computed<HomeInfoSection[]>(() =>
  buildIntroSections(t, isLogin.value),
);

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

const resolveNavHeight = (): number => {
  const rawValue = window
    .getComputedStyle(document.documentElement)
    .getPropertyValue("--nav-height");
  const parsedValue = Number.parseFloat(rawValue);

  return Number.isFinite(parsedValue) ? parsedValue : 0;
};

const resolveDocumentHeight = (): number =>
  Math.max(
    document.documentElement.scrollHeight,
    document.body?.scrollHeight ?? 0,
  );

const scrollToSectionContent = (key: HomeSectionKey) => {
  const target = document.getElementById(sectionContentId(key));

  if (!target) {
    return;
  }

  window.scrollTo({
    top: resolveHomeSectionScrollTop({
      currentScrollY: window.scrollY,
      targetTop: target.getBoundingClientRect().top,
      viewportHeight: window.innerHeight,
      documentHeight: resolveDocumentHeight(),
      navHeight: resolveNavHeight(),
    }),
    behavior: prefersReducedMotion ? "auto" : "smooth",
  });
};

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
}

@media (max-width: 768px) {
  .home-page {
    padding-bottom: 2rem;
  }

  .home-section,
  .workflow-section {
    min-height: auto;
    margin-top: 0.85rem;
  }

  .workflow-section {
    padding-block: 1.3rem 1.45rem;
  }

  .workflow-grid {
    grid-template-columns: 1fr;
  }

  .product-section {
    padding-block: 1.35rem;
  }
}
</style>
