<template>
  <section class="filter-card ui-surface-glass">
    <div class="filter-head">
      <h2>风险域切换</h2>
      <p>默认展示首个风险域，点击标签可切换查看对应评测项。</p>
    </div>

    <div class="chip-row">
      <button
        v-for="category in categories"
        :key="category.categoryId"
        type="button"
        class="category-chip ui-btn ui-btn-pill"
        :class="{ active: activeCategoryId === category.categoryId }"
        :style="getChipStyle(category.categoryId, activeCategoryId === category.categoryId)"
        @click="$emit('select-category', category.categoryId)"
      >
        <span class="chip-name">{{ category.name }}</span>
        <span class="chip-meaning">{{ category.meaning }}</span>
      </button>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { DatasetCategoryViewModel } from "@/shared/types/DatasetTypes";
import { getCategoryTheme } from "@/modules/dataset/lib";

defineEmits<{
  (event: "select-category", categoryId: string): void;
}>();

defineProps<{
  categories: DatasetCategoryViewModel[];
  activeCategoryId: string;
}>();

const getChipStyle = (categoryId: string, active: boolean) => {
  const theme = getCategoryTheme(categoryId);

  if (active) {
    return {
      background: theme.gradient,
      color: "#ffffff",
      border: `1px solid ${theme.solid}`,
      boxShadow: `0 12px 24px -24px ${theme.shadow}`,
    };
  }

  return {
    background: `linear-gradient(180deg, ${theme.soft}, #ffffff)`,
    color: theme.text,
    border: `1px solid ${theme.border}`,
    boxShadow: `0 8px 16px -24px ${theme.shadow}`,
  };
};
</script>

<style scoped>
.filter-card {
  border-radius: 2rem;
  padding: 1.4rem;
  margin-bottom: 1.8rem;
}

.filter-head h2 {
  margin: 0;
  color: #0f172a;
  font-size: 1.08rem;
}

.filter-head p {
  margin: 0.45rem 0 0;
  color: #64748b;
  line-height: 1.7;
}

.chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.85rem;
  margin-top: 1rem;
}

.category-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.55rem;
  padding: 0.85rem 1.15rem;
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease,
    border-color 0.2s ease;
}

.category-chip:hover {
  transform: translateY(-1px);
}

.chip-name {
  font-weight: 700;
}

.chip-meaning {
  opacity: 0.86;
  font-size: 0.88rem;
}

@media (max-width: 768px) {
  .filter-card {
    padding: 1.15rem;
  }
}
</style>
