<template>
  <section class="category-section">
    <header class="category-header ui-glow-frame" :style="headerStyle">
      <div class="category-copy">
        <div class="title-row">
          <h2>{{ category.name }}</h2>
          <span class="meaning">{{ category.meaning }}</span>
        </div>
        <p class="description">{{ category.description }}</p>
      </div>

      <div class="stat-card ui-surface-white" :style="statCardStyle">
        <span>评测项数量</span>
        <strong>{{ category.subcategories.length }}</strong>
      </div>
    </header>

    <div class="grid-auto-fit category-grid">
      <DatasetSubcategoryCard
        v-for="dataset in category.subcategories"
        :key="dataset.datasetId"
        :dataset="dataset"
        :category="category"
      />
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { DatasetCategoryViewModel } from "@/shared/types/dataset-types";
import { getCategoryTheme } from "@/modules/dataset/lib/dataset-utils";
import DatasetSubcategoryCard from "@/modules/dataset/components/DatasetSubcategoryCard.vue";

const props = defineProps<{
  category: DatasetCategoryViewModel;
}>();

const headerStyle = computed(() => {
  const theme = getCategoryTheme(props.category.categoryId);

  return {
    backgroundImage: `linear-gradient(135deg, ${theme.soft}, rgba(255, 255, 255, 0.92))`,
    boxShadow: `0 20px 38px -30px ${theme.shadow}`,
    "--category-solid": theme.solid,
  };
});

const statCardStyle = computed(() => {
  const theme = getCategoryTheme(props.category.categoryId);

  return {
    border: `1px solid ${theme.border}`,
    boxShadow: `0 14px 24px -26px ${theme.shadow}`,
  };
});
</script>

<style scoped lang="scss">
.category-section + .category-section {
  margin-top: 2rem;
}

.category-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1.25rem;
  padding: 1.4rem;
  border-radius: 1.7rem;
  border: 1px solid rgba(255, 255, 255, 0.72);
}

.category-copy {
  min-width: 0;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.title-row h2 {
  margin: 0;
  color: var(--color-text-dark);
  font-size: 1.72rem;
}

.meaning {
  padding: 0.3rem 0.7rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.76);
  color: var(--color-primary);
  font-size: 0.82rem;
  font-weight: 700;
}

.description {
  margin: 0.75rem 0 0;
  max-width: 760px;
  color: var(--color-text-muted);
  line-height: 1.8;
}

.stat-card {
  min-width: 120px;
  padding: 1rem;
  border-radius: 1rem;
  color: var(--color-text-dark);
  text-align: center;
}

.stat-card span {
  display: block;
  color: var(--color-text-subtle);
  font-size: 0.8rem;
}

.stat-card strong {
  display: block;
  margin-top: 0.35rem;
  font-size: 1.5rem;
}

.category-grid {
  --grid-min-size: 280px;
  --grid-gap: 1rem;
  margin-top: 1rem;
}

@media (max-width: 768px) {
  .category-header {
    flex-direction: column;
  }

  .stat-card {
    width: 100%;
  }
}
</style>
