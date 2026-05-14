<template>
  <div class="category-list">
    <SubmitDatasetCategoryBlock
      v-for="category in categories"
      :key="category.categoryId"
      :category="category"
      :selected-dataset-ids="selectedDatasetIds"
      :expanded="expandedCategoryIds.includes(category.categoryId)"
      @toggle-category="$emit('toggle-category', $event)"
      @toggle-dataset="$emit('toggle-dataset', $event)"
      @toggle-expanded="$emit('toggle-expanded', $event)"
    />
  </div>
</template>

<script setup lang="ts">
import SubmitDatasetCategoryBlock from "@/modules/submission/components/SubmitDatasetCategoryBlock.vue";
import type { DatasetCategory } from "@/shared/types/dataset-types";

defineProps<{
  categories: DatasetCategory[];
  selectedDatasetIds: string[];
  expandedCategoryIds: string[];
}>();

defineEmits<{
  (event: "toggle-category", categoryId: string): void;
  (event: "toggle-dataset", datasetId: string): void;
  (event: "toggle-expanded", categoryId: string): void;
}>();
</script>

<style scoped lang="scss">
.category-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
</style>
