<template>
  <section class="tree-card ui-surface-white">
    <div class="tree-header">
      <div>
        <h3>评测目录</h3>
        <p>按当前攻击难度展示可选风险域与评测项，仅保留当前仍有效的已选交集。</p>
      </div>
      <div class="header-actions">
        <button
          class="header-btn ui-btn ui-btn-pill"
          type="button"
          :disabled="!categories.length"
          @click="$emit('select-all')"
        >
          全选
        </button>
        <button
          class="header-btn ui-btn ui-btn-pill"
          type="button"
          :disabled="!selectedDatasetIds.length"
          @click="$emit('clear-all')"
        >
          清空
        </button>
      </div>
    </div>

    <div class="status-list">
      <p v-if="syncMessage" class="status-banner sync">{{ syncMessage }}</p>
      <p
        v-if="status === 'refreshing'"
        class="status-banner refreshing"
      >
        正在按当前难度刷新可用评测项…
      </p>
      <div v-if="status === 'loading' && !categories.length" class="state-card">
        <h4>正在加载可用评测项</h4>
        <p>系统正在根据当前攻击难度筛选风险域与评测项，请稍候。</p>
      </div>
      <div v-else-if="status === 'error' && !categories.length" class="state-card">
        <h4>评测目录加载失败</h4>
        <p>{{ errorMessage || "请重试后继续提交。" }}</p>
        <button class="retry-btn ui-btn ui-btn-pill" type="button" @click="$emit('retry')">
          重试
        </button>
      </div>
      <div v-else-if="status === 'empty'" class="state-card">
        <h4>当前难度下暂无可用评测项</h4>
        <p>请调整攻击难度后重试；在无可用评测项时无法提交。</p>
      </div>
      <p v-else-if="status === 'error'" class="status-banner error">
        {{ errorMessage || "目录刷新失败，请重试。" }}
        <button class="inline-retry" type="button" @click="$emit('retry')">
          重新加载
        </button>
      </p>
    </div>

    <template v-if="categories.length">
      <div class="summary-bar">
        <span>已选风险域 {{ selectedCategoryCount }}</span>
        <span>已选评测项 {{ selectedDatasetIds.length }}</span>
        <span>总评测项 {{ totalDatasetCount }}</span>
      </div>

      <div class="category-list">
        <article
          v-for="category in categories"
          :key="category.categoryId"
          class="category-block"
          :style="getCategoryBlockStyle(category.categoryId)"
        >
          <div class="category-row">
            <label class="category-main">
              <input
                type="checkbox"
                class="category-checkbox"
                :checked="isFullySelected(category)"
                @change="$emit('toggle-category', category.categoryId)"
              />
              <span class="category-name">{{ category.name }}</span>
              <span class="category-meaning">{{ category.meaning }}</span>
            </label>

            <div class="category-right">
              <span class="category-state" :class="getCategoryState(category)">
                {{ getCategoryStateLabel(category) }}
              </span>
              <button
                class="expand-btn"
                type="button"
                @click="$emit('toggle-expanded', category.categoryId)"
              >
                {{ expandedCategoryIds.includes(category.categoryId) ? "收起" : "展开" }}
              </button>
            </div>
          </div>

          <div
            v-if="expandedCategoryIds.includes(category.categoryId)"
            class="dataset-list"
          >
            <label
              v-for="dataset in category.subcategories"
              :key="dataset.datasetId"
              class="dataset-item"
            >
              <input
                type="checkbox"
                :checked="selectedDatasetIds.includes(dataset.datasetId)"
                @change="$emit('toggle-dataset', dataset.datasetId)"
              />
              <div class="dataset-copy">
                <span class="dataset-name">{{ dataset.name }}</span>
                <span class="dataset-description">{{ dataset.shortDescription }}</span>
              </div>
            </label>
          </div>
        </article>
      </div>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { DatasetCategoryViewModel } from "@/types/DatasetTypes";
import type { SubmitDatasetCatalogStatus } from "@/composables/useSubmitDatasetCatalog";
import {
  getCategoryTheme,
  isCategoryFullySelected,
  isCategoryPartiallySelected,
} from "@/utils/DatasetUtils";

const props = defineProps<{
  categories: DatasetCategoryViewModel[];
  selectedDatasetIds: string[];
  expandedCategoryIds: string[];
  status: SubmitDatasetCatalogStatus;
  errorMessage?: string;
  syncMessage?: string;
}>();

defineEmits<{
  (event: "select-all"): void;
  (event: "clear-all"): void;
  (event: "toggle-category", categoryId: string): void;
  (event: "toggle-dataset", datasetId: string): void;
  (event: "toggle-expanded", categoryId: string): void;
  (event: "retry"): void;
}>();

const totalDatasetCount = computed(() =>
  props.categories.reduce(
    (sum, category) => sum + category.subcategories.length,
    0,
  ),
);

const selectedCategoryCount = computed(
  () =>
    props.categories.filter((category) =>
      category.subcategories.some((item) =>
        props.selectedDatasetIds.includes(item.datasetId),
      ),
    ).length,
);

const isFullySelected = (category: DatasetCategoryViewModel) =>
  isCategoryFullySelected(category, props.selectedDatasetIds);

const isPartiallySelected = (category: DatasetCategoryViewModel) =>
  isCategoryPartiallySelected(category, props.selectedDatasetIds);

const getCategoryState = (category: DatasetCategoryViewModel) => {
  if (isFullySelected(category)) return "all";
  if (isPartiallySelected(category)) return "partial";
  return "empty";
};

const getCategoryStateLabel = (category: DatasetCategoryViewModel) => {
  if (isFullySelected(category)) return "全选";
  if (isPartiallySelected(category)) return "半选";
  return "未选";
};

const getCategoryBlockStyle = (categoryId: string) => {
  const theme = getCategoryTheme(categoryId);

  return {
    "--category-soft": theme.soft,
    "--category-border": theme.border,
    "--category-text": theme.text,
    "--category-solid": theme.solid,
    "--category-gradient": theme.gradient,
    "--category-shadow": theme.shadow,
  };
};
</script>

<style scoped>
.tree-card {
  border-radius: 1.8rem;
  padding: 1.4rem;
}

.tree-header {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: flex-start;
}

.tree-header h3 {
  margin: 0;
  color: #0f172a;
  font-size: 1.15rem;
}

.tree-header p {
  margin: 0.45rem 0 0;
  color: #64748b;
  line-height: 1.6;
}

.header-actions {
  display: flex;
  gap: 0.7rem;
}

.header-btn {
  background: #f8fafc;
  border: 1px solid #cbd5e1;
  color: #334155;
  padding: 0.66rem 0.95rem;
}

.header-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.status-list {
  display: flex;
  flex-direction: column;
  gap: 0.7rem;
  margin-top: 1rem;
}

.status-banner,
.state-card {
  border-radius: 1rem;
  padding: 0.95rem 1rem;
}

.status-banner {
  margin: 0;
  font-weight: 600;
}

.status-banner.sync {
  background: rgba(255, 237, 213, 0.9);
  color: #c2410c;
}

.status-banner.refreshing {
  background: rgba(219, 234, 254, 0.9);
  color: #1d4ed8;
}

.status-banner.error,
.state-card {
  background: rgba(254, 242, 242, 0.92);
  color: #b91c1c;
}

.state-card h4 {
  margin: 0;
  color: #0f172a;
}

.state-card p {
  margin: 0.45rem 0 0;
  line-height: 1.7;
}

.retry-btn,
.inline-retry {
  margin-top: 0.75rem;
  border: 1px solid #cbd5e1;
  background: #ffffff;
  color: #334155;
}

.inline-retry {
  margin: 0 0 0 0.8rem;
  padding: 0;
  border: none;
  background: transparent;
  color: inherit;
  font: inherit;
  text-decoration: underline;
  cursor: pointer;
}

.summary-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 0.8rem;
  margin-top: 1rem;
  color: #475569;
  font-size: 0.9rem;
}

.category-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-top: 1.15rem;
}

.category-block {
  position: relative;
  border: 1px solid var(--category-border, #e2e8f0);
  border-radius: 1.3rem;
  overflow: hidden;
  box-shadow: 0 12px 24px -28px var(--category-shadow, rgba(15, 23, 42, 0.22));
}

.category-block::before {
  content: "";
  display: block;
  height: 3px;
  background: var(
    --category-gradient,
    linear-gradient(135deg, #2563eb, #7c3aed)
  );
}

.category-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 1rem 1.05rem;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(255, 255, 255, 0.92)),
    linear-gradient(90deg, var(--category-soft, #f8fafc), #ffffff 72%);
}

.category-main {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  min-width: 0;
}

.category-checkbox,
.dataset-item input {
  width: 18px;
  height: 18px;
  accent-color: var(--category-solid, #2563eb);
  flex-shrink: 0;
}

.category-name {
  color: #0f172a;
  font-weight: 700;
}

.category-meaning {
  color: var(--category-text, #64748b);
  font-size: 0.88rem;
}

.category-right {
  display: flex;
  align-items: center;
  gap: 0.8rem;
}

.category-state {
  border-radius: 999px;
  padding: 0.28rem 0.68rem;
  font-size: 0.8rem;
  font-weight: 700;
}

.category-state.all {
  background: linear-gradient(90deg, var(--category-soft, #dcfce7), #ffffff);
  color: var(--category-text, #15803d);
}

.category-state.partial {
  background: linear-gradient(
    90deg,
    var(--category-soft, #dbeafe),
    rgba(255, 255, 255, 0.92)
  );
  color: var(--category-solid, #1d4ed8);
}

.category-state.empty {
  background: #e2e8f0;
  color: #475569;
}

.expand-btn {
  border: none;
  background: transparent;
  color: var(--category-solid, #2563eb);
  font-weight: 700;
  cursor: pointer;
}

.dataset-list {
  display: grid;
  gap: 0.8rem;
  padding: 1rem 1.05rem;
  background: linear-gradient(180deg, var(--category-soft, #f8fafc), #ffffff 84%);
}

.dataset-item {
  display: flex;
  align-items: flex-start;
  gap: 0.8rem;
  padding: 0.9rem;
  border-radius: 1rem;
  background: linear-gradient(180deg, #ffffff 0%, var(--category-soft, #f8fafc) 130%);
  border: 1px solid var(--category-border, #e2e8f0);
  box-shadow: 0 8px 16px -28px var(--category-shadow, rgba(15, 23, 42, 0.18));
}

.dataset-copy {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.dataset-name {
  color: #0f172a;
  font-weight: 600;
}

.dataset-description {
  color: #64748b;
  line-height: 1.6;
}

@media (max-width: 768px) {
  .tree-header,
  .category-row {
    flex-direction: column;
    align-items: stretch;
  }

  .header-actions,
  .category-right {
    width: 100%;
    justify-content: space-between;
  }
}
</style>
