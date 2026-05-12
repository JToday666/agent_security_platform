<template>
  <section class="meta-bar">
    <article class="meta-item ui-surface-white">
      <MetricStat
        :label="t('dataset.labels.riskDomain')"
        :value="categoryName"
        :description="categoryMeaning"
      />
    </article>
    <article class="meta-item ui-surface-white">
      <MetricStat
        :label="t('dataset.labels.sampleCount')"
        :value="sampleCount"
        :description="t('dataset.meta.sampleCountDescription')"
      />
    </article>
    <article class="meta-item ui-surface-white">
      <MetricStat
        :label="t('dataset.labels.updatedAt')"
        :value="updatedAt"
        :description="t('dataset.meta.updatedAtDescription')"
      />
    </article>
  </section>
</template>

<script setup lang="ts">
import { useI18n } from "vue-i18n";
import MetricStat from "@/shared/ui/display/MetricStat.vue";

defineProps<{
  categoryName: string;
  categoryMeaning: string;
  sampleCount: string;
  updatedAt: string;
}>();

const { t } = useI18n();
</script>

<style scoped lang="scss">
.meta-bar {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.85rem;
}

.meta-item {
  border-radius: 1.2rem;
  padding: 1rem 1.05rem;
}

@media (max-width: 900px) {
  .meta-bar {
    grid-template-columns: 1fr;
  }
}
</style>
