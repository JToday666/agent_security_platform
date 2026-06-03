<template>
  <SectionBlock
    class="assets-section"
    :title="t('attackScenarioLibrary.pages.detail.sections.assets')"
  >
    <div v-if="hasAnyAssets" class="assets-shell">
      <div
        v-if="availablePanels.length > 1"
        class="assets-tabs"
        :aria-label="t('attackScenarioLibrary.resources.tabsAria')"
      >
        <button
          v-for="panel in availablePanels"
          :key="panel.value"
          type="button"
          :aria-pressed="activePanel === panel.value"
          :class="{ active: activePanel === panel.value }"
          @click="activePanel = panel.value"
        >
          {{ panel.label }}
        </button>
      </div>

      <div
        class="assets-panel"
      >
        <EvaluationItemResourcesList
          v-if="activePanel === 'resources'"
          :resources="resources"
        />
        <EvaluationItemMediaGallery v-else :media="media" />
      </div>
    </div>

    <InlineNotice
      v-else
      tone="info"
      :title="t('attackScenarioLibrary.resources.emptyTitle')"
      :message="t('attackScenarioLibrary.resources.emptyMessage')"
    />
  </SectionBlock>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import EvaluationItemMediaGallery from "@/modules/attack-scenario-library/components/EvaluationItemMediaGallery.vue";
import EvaluationItemResourcesList from "@/modules/attack-scenario-library/components/EvaluationItemResourcesList.vue";
import type {
  EvaluationItemMediaItem,
  EvaluationItemResourceLink,
} from "@/shared/types/attack-scenario-library-types";
import InlineNotice from "@/shared/ui/feedback/InlineNotice.vue";
import SectionBlock from "@/shared/ui/page/SectionBlock.vue";

type AssetPanel = "resources" | "media";

const props = defineProps<{
  resources: EvaluationItemResourceLink[];
  media: EvaluationItemMediaItem[];
}>();

const { t } = useI18n();

const hasResources = computed(() => props.resources.length > 0);
const hasMedia = computed(() => props.media.length > 0);
const hasAnyAssets = computed(() => hasResources.value || hasMedia.value);

const availablePanels = computed<Array<{ label: string; value: AssetPanel }>>(
  () => [
    ...(hasResources.value
      ? [
          {
            label: t("attackScenarioLibrary.resources.tab"),
            value: "resources" as const,
          },
        ]
      : []),
    ...(hasMedia.value
      ? [
          {
            label: t("attackScenarioLibrary.media.tab"),
            value: "media" as const,
          },
        ]
      : []),
  ],
);

const resolveActivePanel = (): AssetPanel =>
  hasResources.value ? "resources" : "media";

const activePanel = ref<AssetPanel>(resolveActivePanel());

watch(
  availablePanels,
  (panels) => {
    if (!panels.some((panel) => panel.value === activePanel.value)) {
      activePanel.value = resolveActivePanel();
    }
  },
  { immediate: true },
);
</script>

<style scoped lang="scss">
.assets-section :deep(.section-block__body) {
  gap: 1rem;
}

.assets-shell {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 1rem;
}

.assets-tabs {
  display: inline-flex;
  width: fit-content;
  max-width: 100%;
  gap: 0.25rem;
  padding: 0.2rem;
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: var(--radius-pill);
  background: rgba(255, 255, 255, 0.72);
  box-shadow: 0 14px 28px -26px rgba(15, 23, 42, 0.26);
}

.assets-tabs button {
  min-height: 2.35rem;
  padding: 0 0.9rem;
  border: 0;
  border-radius: var(--radius-pill);
  background: transparent;
  color: var(--color-text-muted);
  cursor: pointer;
  font-weight: 700;
  transition:
    background var(--duration-base) var(--ease-standard),
    color var(--duration-base) var(--ease-standard),
    box-shadow var(--duration-base) var(--ease-standard);
}

.assets-tabs button:hover {
  color: var(--color-primary);
}

.assets-tabs button.active {
  background: var(--color-white);
  color: var(--color-primary);
  box-shadow: var(--shadow-control);
}

.assets-panel {
  min-width: 0;
}

@media (max-width: 640px) {
  .assets-tabs {
    width: 100%;
    overflow-x: auto;
  }

  .assets-tabs button {
    flex: 1;
    min-width: max-content;
  }
}
</style>
