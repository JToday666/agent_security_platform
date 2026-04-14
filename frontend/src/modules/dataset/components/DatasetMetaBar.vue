<template>
  <section class="meta-bar ui-surface-white">
    <MetricCard label="风险域" :value="categoryName" :description="categoryMeaning" />
    <MetricCard label="样本数" :value="sampleCount" description="用于构成本数据集的样本总量。" />
    <MetricCard label="最近更新" :value="updatedAt" description="以当前接口返回时间为准。" />
  </section>
</template>

<script setup lang="ts">
import MetricCard from "@/shared/ui/display/MetricCard.vue";

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
  padding: 0;
  background: transparent;
  border: none;
  box-shadow: none;
}

@media (max-width: 900px) {
  .meta-bar {
    grid-template-columns: 1fr;
  }
}
</style>
