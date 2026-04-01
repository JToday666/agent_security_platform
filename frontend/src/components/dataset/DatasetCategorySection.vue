<template>
  <section class="category-section">
    <header class="category-header" :style="headerStyle">
      <div>
        <div class="title-row">
          <h2>{{ category.name }}</h2>
          <span class="meaning">{{ category.meaning }}</span>
        </div>
        <p class="description">{{ category.description }}</p>
      </div>
      <div class="stat-card ui-surface-white">
        <span>小类数量</span>
        <strong>{{ category.subcategories.length }}</strong>
      </div>
    </header>

    <div class="card-grid">
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
import type { DatasetCategoryViewModel } from "@/types/DatasetTypes";
import { getCategoryThemeByIndex } from "@/utils/DatasetUtils";
import DatasetSubcategoryCard from "@/components/dataset/DatasetSubcategoryCard.vue";

const props = defineProps<{
  category: DatasetCategoryViewModel;
}>();

const headerStyle = computed(() => {
  const theme = getCategoryThemeByIndex(props.category.themeIndex);

  return {
    backgroundImage: theme.gradient,
    boxShadow: `0 20px 40px -20px ${theme.solid}80`,
  };
});
</script>

<style scoped>
.category-section + .category-section {
  margin-top: 2.2rem;
}

.category-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1.25rem;
  padding: 1.6rem;
  border-radius: 1.8rem;
  color: #ffffff;
  box-shadow: 0 18px 36px -18px rgba(37, 99, 235, 0.5);
}

.title-row {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  flex-wrap: wrap;
}

.title-row h2 {
  margin: 0;
  font-size: 1.8rem;
}

.meaning {
  padding: 0.3rem 0.75rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.18);
  font-size: 0.88rem;
  font-weight: 700;
}

.description {
  margin: 0.8rem 0 0;
  max-width: 760px;
  color: rgba(255, 255, 255, 0.92);
  line-height: 1.7;
}

.stat-card {
  min-width: 110px;
  padding: 1rem;
  border-radius: 1rem;
  color: #0f172a;
  text-align: center;
}

.stat-card span {
  display: block;
  color: #64748b;
  font-size: 0.82rem;
}

.stat-card strong {
  display: block;
  margin-top: 0.35rem;
  font-size: 1.5rem;
}

.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1rem;
  margin-top: 1.1rem;
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
