<template>
  <div class="category-list">
    <SubmitDatasetCategoryBlock
      v-for="category in categories"
      :key="category.categoryId"
      :category="category"
      :theme="resolveCategoryTheme(category.categoryId)"
      :selected-dataset-ids="selectedDatasetIds"
      :expanded="expandedCategoryIds.includes(category.categoryId)"
      @toggle-category="$emit('toggle-category', $event)"
      @toggle-dataset="$emit('toggle-dataset', $event)"
      @toggle-expanded="$emit('toggle-expanded', $event)"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import {
  getCategoryTheme,
  getCategoryThemeMap,
} from "@/modules/dataset/lib/dataset-utils";
import SubmitDatasetCategoryBlock from "@/modules/submission/components/SubmitDatasetCategoryBlock.vue";
import type { DatasetCategory } from "@/shared/types/dataset-types";

const props = defineProps<{
  categories: DatasetCategory[];
  selectedDatasetIds: string[];
  expandedCategoryIds: string[];
}>();

defineEmits<{
  (event: "toggle-category", categoryId: string): void;
  (event: "toggle-dataset", datasetId: string): void;
  (event: "toggle-expanded", categoryId: string): void;
}>();

const categoryThemeIds = computed(() =>
  props.categories.map((category) => category.categoryId),
);

const categoryThemeMap = computed(() => getCategoryThemeMap(categoryThemeIds.value));

const resolveCategoryTheme = (categoryId: string) =>
  categoryThemeMap.value.get(categoryId) ??
  getCategoryTheme(categoryId, categoryThemeIds.value);
</script>

<style scoped lang="scss">
.category-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
</style>
