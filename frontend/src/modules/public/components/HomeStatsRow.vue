<template>
  <section class="stats-row">
    <MetricCard
      v-for="item in items"
      :key="item.label"
      :label="item.label"
      :value="item.value"
      :description="item.description"
    />
  </section>
</template>

<script setup lang="ts">
import MetricCard from "@/shared/ui/display/MetricCard.vue";

defineProps<{
  items: Array<{
    label: string;
    value: string;
    description: string;
  }>;
}>();
</script>

<style scoped>
.stats-row {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.85rem;
}

@media (max-width: 1080px) {
  .stats-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .stats-row {
    grid-template-columns: 1fr;
  }
}
</style>
