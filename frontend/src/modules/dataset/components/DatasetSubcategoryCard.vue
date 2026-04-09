<template>
  <router-link
    :to="RouteLocation.datasetDetail(dataset.datasetId)"
    class="dataset-card ui-surface-white"
    :style="cardStyle"
  >
    <div class="card-top">
      <span class="category-badge" :style="badgeStyle">{{ category.name }}</span>
    </div>

    <h3 class="dataset-name">{{ dataset.name }}</h3>
    <p class="dataset-description">{{ dataset.shortDescription || "暂无说明" }}</p>

    <div class="grid-cols-2" style="gap: 0.8rem; margin-top: 1.2rem;">
      <div class="meta-item">
        <span class="meta-label">样本数</span>
        <strong>{{ formatSampleCount(dataset.sampleCount ?? undefined) }}</strong>
      </div>
      <div class="meta-item">
        <span class="meta-label">更新时间</span>
        <strong>{{ formatDateLabel(dataset.updatedAt ?? undefined) }}</strong>
      </div>
    </div>

    <span class="detail-link">
      查看详情
      <span class="detail-arrow">→</span>
    </span>
  </router-link>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { RouteLocation } from "@/app/router/RouteNames";
import type {
  DatasetCategoryViewModel,
  DatasetSubcategory,
} from "@/shared/types/DatasetTypes";
import {
  formatDateLabel,
  formatSampleCount,
  getCategoryTheme,
} from "@/modules/dataset/lib";

const props = defineProps<{
  dataset: DatasetSubcategory;
  category: DatasetCategoryViewModel;
}>();

const theme = computed(() => getCategoryTheme(props.category.categoryId));

const cardStyle = computed(() => ({
  "--dataset-soft": theme.value.soft,
  "--dataset-border": theme.value.border,
  "--dataset-text": theme.value.text,
  "--dataset-solid": theme.value.solid,
  "--dataset-shadow": theme.value.shadow,
}));

const badgeStyle = computed(() => {
  return {
    background: theme.value.soft,
    color: theme.value.text,
    border: `1px solid ${theme.value.border}`,
  };
});
</script>

<style scoped>
.dataset-card {
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 260px;
  padding: 1.4rem;
  border-radius: 1.4rem;
  text-decoration: none;
  color: inherit;
  border: 1px solid var(--dataset-border, rgba(226, 232, 240, 0.88));
  box-shadow: 0 10px 20px -26px var(--dataset-shadow, rgba(15, 23, 42, 0.16));
  transition:
    transform 0.22s ease,
    box-shadow 0.22s ease,
    border-color 0.22s ease;
}

.dataset-card::before {
  content: "";
  position: absolute;
  inset: 0 0 auto;
  height: 3px;
  background: linear-gradient(
    90deg,
    var(--dataset-solid, #2563eb),
    var(--dataset-border, #93c5fd)
  );
}

.dataset-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 16px 28px -22px var(--dataset-shadow, rgba(15, 23, 42, 0.2));
}

.card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.category-badge {
  border-radius: 999px;
  padding: 0.34rem 0.7rem;
  font-size: 0.8rem;
  font-weight: 600;
}

.dataset-name {
  margin: 1rem 0 0.7rem;
  color: #0f172a;
  font-size: 1.3rem;
}

.dataset-description {
  margin: 0;
  color: #475569;
  line-height: 1.7;
  flex: 1;
}

.meta-item {
  padding: 0.9rem;
  background: linear-gradient(180deg, var(--dataset-soft, #f8fafc), #ffffff 84%);
  border: 1px solid var(--dataset-border, #e2e8f0);
  border-radius: 1rem;
}

.meta-label {
  display: block;
  color: #64748b;
  font-size: 0.8rem;
  margin-bottom: 0.35rem;
}

.meta-item strong {
  color: #0f172a;
  font-size: 0.98rem;
}

.detail-link {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  margin-top: 1.1rem;
  color: var(--dataset-solid, #2563eb);
  font-weight: 700;
}

.detail-arrow {
  transition: transform 0.2s ease;
}

.dataset-card:hover .detail-arrow {
  transform: translateX(3px);
}

@media (max-width: 640px) {
  .meta-list {
    grid-template-columns: 1fr;
  }
}
</style>
