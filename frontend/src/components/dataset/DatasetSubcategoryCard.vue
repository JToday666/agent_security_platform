<template>
  <router-link
    :to="RouteLocation.datasetDetail(dataset.datasetId)"
    class="dataset-card ui-surface-white"
  >
    <div class="card-top">
      <span class="category-badge" :style="badgeStyle">{{ category.name }}</span>
      <span class="dataset-id">{{ dataset.datasetId }}</span>
    </div>

    <h3 class="dataset-name">{{ dataset.name }}</h3>
    <p class="dataset-description">{{ dataset.shortDescription }}</p>

    <div class="meta-list">
      <div class="meta-item">
        <span class="meta-label">样本数</span>
        <strong>{{ formatSampleCount(dataset.sampleCount) }}</strong>
      </div>
      <div class="meta-item">
        <span class="meta-label">更新时间</span>
        <strong>{{ formatDateLabel(dataset.updatedAt) }}</strong>
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
import { RouteLocation } from "@/router/RouteNames";
import type { DatasetCategoryViewModel, DatasetSubcategory } from "@/types/DatasetTypes";
import {
  formatDateLabel,
  formatSampleCount,
  getCategoryThemeByIndex,
} from "@/utils/DatasetUtils";

const props = defineProps<{
  dataset: DatasetSubcategory;
  category: DatasetCategoryViewModel;
}>();

// 卡片顶部的大类徽标颜色和数据集所属大类保持一致。
const badgeStyle = computed(() => {
  const theme = getCategoryThemeByIndex(props.category.themeIndex);
  return {
    background: theme.soft,
    color: theme.text,
    border: `1px solid ${theme.border}`,
  };
});
</script>

<style scoped>
.dataset-card {
  display: flex;
  flex-direction: column;
  min-height: 260px;
  padding: 1.4rem;
  border-radius: 1.4rem;
  text-decoration: none;
  color: inherit;
  border: 1px solid rgba(226, 232, 240, 0.88);
  transition:
    transform 0.22s ease,
    box-shadow 0.22s ease;
}

.dataset-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 18px 36px -14px rgba(15, 23, 42, 0.16);
}

.card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.category-badge,
.dataset-id {
  border-radius: 999px;
  padding: 0.34rem 0.7rem;
  font-size: 0.8rem;
  font-weight: 600;
}

.dataset-id {
  background: #f8fafc;
  color: #64748b;
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

.meta-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.8rem;
  margin-top: 1.2rem;
}

.meta-item {
  padding: 0.9rem;
  background: #f8fafc;
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
  color: #2563eb;
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
