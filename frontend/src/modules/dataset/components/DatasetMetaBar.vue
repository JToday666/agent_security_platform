<template>
  <section class="meta-bar">
    <article class="meta-item ui-surface-white">
      <MetricStat label="风险域" :value="categoryName" :description="categoryMeaning" />
    </article>
    <article class="meta-item ui-surface-white">
      <MetricStat
        label="样本数"
        :value="sampleCount"
        description="用于构成本数据集的样本总量。"
      />
    </article>
    <article class="meta-item ui-surface-white">
      <MetricStat
        label="最近更新"
        :value="updatedAt"
        description="以当前接口返回时间为准。"
      />
    </article>
  </section>
</template>

<script setup lang="ts">
import MetricStat from "@/shared/ui/display/MetricStat.vue";

defineProps<{
  categoryName: string;
  categoryMeaning: string;
  sampleCount: string;
  updatedAt: string;
}>();
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
