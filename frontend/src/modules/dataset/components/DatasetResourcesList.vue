<template>
  <section class="resources-section">
    <div class="layout-section-head">
      <h2>{{ t("dataset.resources.title") }}</h2>
      <p>{{ t("dataset.resources.description") }}</p>
    </div>

    <div v-if="resources.length" class="resource-list">
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
          {{ t("dataset.resources.view") }}
        </Button>
      </article>
    </div>

    <InlineNotice
      v-else
      tone="info"
      :title="t('dataset.resources.emptyTitle')"
      :message="t('dataset.resources.emptyMessage')"
    />
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import type { DatasetResourceLink } from "@/shared/types/dataset-types";
import Button from "@/shared/ui/actions/UiButton.vue";
import InlineNotice from "@/shared/ui/feedback/InlineNotice.vue";

defineProps<{
  resources: DatasetResourceLink[];
}>();

const { t } = useI18n();

const typeLabels = computed<Record<DatasetResourceLink["type"], string>>(
  () => ({
    docs: t("dataset.resources.types.docs"),
    download: t("dataset.resources.types.download"),
    demo: t("dataset.resources.types.demo"),
    link: t("dataset.resources.types.link"),
  }),
);
</script>

<style scoped lang="scss">
.resources-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding-top: 1.2rem;
  border-top: 1px solid rgba(148, 163, 184, 0.16);
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

