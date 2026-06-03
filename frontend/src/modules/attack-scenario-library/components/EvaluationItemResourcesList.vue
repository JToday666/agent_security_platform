<template>
  <div class="resources-list-panel">
    <div class="resource-list">
      <article
        v-for="resource in resources"
        :key="resource.label + resource.url"
        class="resource-item"
      >
        <div class="resource-copy">
          <strong>{{ resource.label }}</strong>
          <span>{{ typeLabels[resource.type] }}</span>
        </div>
        <Button :href="resource.url" target="_blank" variant="secondary" size="sm">
          {{ t("attackScenarioLibrary.resources.view") }}
        </Button>
      </article>
    </div>

  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import type { EvaluationItemResourceLink } from "@/shared/types/attack-scenario-library-types";
import Button from "@/shared/ui/actions/UiButton.vue";

defineProps<{
  resources: EvaluationItemResourceLink[];
}>();

const { t } = useI18n();

const typeLabels = computed<Record<EvaluationItemResourceLink["type"], string>>(
  () => ({
    docs: t("attackScenarioLibrary.resources.types.docs"),
    download: t("attackScenarioLibrary.resources.types.download"),
    demo: t("attackScenarioLibrary.resources.types.demo"),
    link: t("attackScenarioLibrary.resources.types.link"),
  }),
);
</script>

<style scoped lang="scss">
.resources-list-panel {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.resource-list {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.resource-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.9rem 1rem;
  border: 1px solid rgba(148, 163, 184, 0.14);
  border-radius: 1rem;
  background: rgba(248, 250, 252, 0.78);
}

.resource-copy {
  display: flex;
  flex-direction: column;
  gap: 0.28rem;
  min-width: 0;
}

.resource-copy strong {
  color: var(--color-text-dark);
}

.resource-copy span {
  color: var(--color-text-subtle);
  font-size: 0.88rem;
}

@media (max-width: 640px) {
  .resource-item {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
