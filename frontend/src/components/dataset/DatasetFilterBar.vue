<template>
  <section class="filter-card ui-surface-glass">
    <div class="summary-row">
      <div class="summary-item ui-surface-white">
        <span>已选风险域</span>
        <strong>{{ selectedCategoryIds.length }}</strong>
      </div>
      <div class="summary-item ui-surface-white">
        <span>已显示评测项</span>
        <strong>{{ visibleDatasetCount }}</strong>
      </div>
      <div class="actions">
        <button class="action-btn ui-btn ui-btn-pill" @click="$emit('select-all')">
          全选
        </button>
        <button class="action-btn ui-btn ui-btn-pill" @click="$emit('clear-all')">
          清空筛选
        </button>
      </div>
    </div>

    <div class="chip-row">
      <button
        v-for="category in categories"
        :key="category.categoryId"
        class="category-chip ui-btn ui-btn-pill"
        :class="{ active: selectedCategoryIds.includes(category.categoryId) }"
        :style="getChipStyle(category.categoryId, selectedCategoryIds.includes(category.categoryId))"
        @click="$emit('toggle-category', category.categoryId)"
      >
        <span class="chip-name">{{ category.name }}</span>
        <span class="chip-meaning">{{ category.meaning }}</span>
      </button>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { DatasetCategoryViewModel } from "@/types/DatasetTypes";
import { getCategoryTheme } from "@/utils/common";

defineEmits<{
  (event: "select-all"): void;
  (event: "clear-all"): void;
  (event: "toggle-category", categoryId: string): void;
}>();

defineProps<{
  categories: DatasetCategoryViewModel[];
  selectedCategoryIds: string[];
  visibleDatasetCount: number;
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

.summary-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.9rem;
  align-items: center;
  justify-content: space-between;
}

.summary-item {
  min-width: 130px;
  padding: 0.95rem 1rem;
  border-radius: 1rem;
}

.summary-item span {
  display: block;
  color: #64748b;
  font-size: 0.86rem;
}

.summary-item strong {
  display: block;
  margin-top: 0.3rem;
  font-size: 1.2rem;
  color: #0f172a;
}

.actions {
  display: flex;
  gap: 0.75rem;
  margin-left: auto;
}

.action-btn {
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(148, 163, 184, 0.35);
  color: #334155;
  padding: 0.72rem 1.1rem;
}

.action-btn:hover {
  transform: translateY(-1px);
}

.chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.8rem;
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
  .summary-row {
    align-items: stretch;
  }

  .summary-item {
    flex: 1 1 120px;
  }

  .actions {
    width: 100%;
    margin-left: 0;
  }

  .action-btn {
    flex: 1;
  }
}
</style>
