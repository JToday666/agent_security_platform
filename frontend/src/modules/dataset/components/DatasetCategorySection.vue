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

      <div class="stat-card" :style="statCardStyle">
        <span>评测项数量</span>
        <strong>{{ category.subcategories.length }}</strong>
      </div>
    </header>

    <div class="category-grid">
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
import DatasetSubcategoryCard from "@/modules/dataset/components/DatasetSubcategoryCard.vue";
import { getCategoryTheme } from "@/modules/dataset/lib/dataset-utils";
import type { DatasetCategoryViewModel } from "@/shared/types/dataset-types";

const props = defineProps<{
  category: DatasetCategoryViewModel;
}>();

const headerStyle = computed(() => {
  const theme = getCategoryTheme(props.category.categoryId);

  return {
    backgroundImage: `linear-gradient(135deg, ${theme.soft}, rgba(255, 255, 255, 0.94))`,
    boxShadow: `0 20px 38px -30px ${theme.shadow}`,
    "--category-solid": theme.solid,
    "--category-border": theme.border,
    "--category-shadow": theme.shadow,
  };
});

const statCardStyle = computed(() => {
  const theme = getCategoryTheme(props.category.categoryId);

  return {
    color: theme.text,
    background: `linear-gradient(180deg, rgba(255, 255, 255, 0.96), ${theme.soft})`,
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
  min-width: 148px;
  padding: 1rem 1.1rem;
  border-radius: 1.1rem;
  text-align: center;
}

.stat-card span {
  display: block;
  font-size: 0.8rem;
  font-weight: 600;
  opacity: 0.82;
}

.stat-card strong {
  display: block;
  margin-top: 0.35rem;
  font-size: 1.6rem;
  line-height: 1;
}

.category-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1.1rem;
  margin-top: 1rem;
}

@media (max-width: 1024px) {
  .category-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .category-header {
    flex-direction: column;
  }

  .stat-card,
  .category-grid {
    width: 100%;
  }

  .category-grid {
    grid-template-columns: 1fr;
  }
}
</style>
