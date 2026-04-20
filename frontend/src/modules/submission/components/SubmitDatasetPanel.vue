<template>
  <SectionCard
    title="数据集选择"
    description="选择本次评测需要覆盖的数据集，可按名称快速筛选。"
  >
    <template #actions>
      <UiButton
        variant="secondary"
        size="sm"
        :disabled="!categories.length"
        @click="$emit('select-all')"
      >
        全选
      </UiButton>
      <UiButton
        variant="secondary"
        size="sm"
        :disabled="!selectedDatasetIds.length"
        @click="$emit('clear-all')"
      >
        清空
      </UiButton>
    </template>

    <div class="toolbar">
      <FormField
        label="搜索"
        :model-value="search"
        type="search"
        placeholder="按风险域、数据集名称或摘要搜索"
        leading-icon="lucide:search"
        @update:model-value="search = $event.trim()"
      />

      <div class="toolbar-metrics">
        <span>已选风险域 {{ selectedCategoryCount }}</span>
        <span>已选数据集 {{ selectedDatasetIds.length }}</span>
        <span>当前结果 {{ visibleDatasetCount }}</span>
      </div>
    </div>

    <div class="status-list">
      <InlineNotice
        v-if="selectionErrorMessage"
        tone="danger"
        :message="selectionErrorMessage"
      />
      <InlineNotice
        v-if="status === 'refreshing'"
        tone="info"
        message="正在刷新可用数据集。"
      />
      <PageStateCard
        v-if="status === 'loading' && !categories.length"
        title="正在加载数据集"
        message="请稍候。"
        :loading="true"
      />
      <PageStateCard
        v-else-if="status === 'error' && !categories.length"
        title="数据集目录加载失败"
        :message="errorMessage || '请重试后继续提交。'"
        action-text="重试"
        action-variant="secondary"
        @action="$emit('retry')"
      />
      <PageStateCard
        v-else-if="status === 'empty'"
        title="当前没有可用数据集"
        message="请稍后重试。"
      />
      <InlineNotice
        v-else-if="status === 'error'"
        tone="danger"
        :message="errorMessage || '目录刷新失败，请重试。'"
      >
        <template #actions>
          <UiButton variant="text" size="sm" @click="$emit('retry')">
            重新加载
          </UiButton>
        </template>
      </InlineNotice>
    </div>

    <template v-if="filteredCategories.length">
      <div class="category-list">
        <article
          v-for="category in filteredCategories"
          :key="category.categoryId"
          class="category-block"
          :style="getCategoryBlockStyle(category.categoryId)"
        >
          <div class="category-row">
            <label class="category-main">
              <input
                type="checkbox"
                class="selection-input"
                :checked="isFullySelected(category)"
                @change="$emit('toggle-category', category.categoryId)"
              />
              <span
                class="selection-box"
                :class="{
                  'selection-box--checked': isFullySelected(category),
                  'selection-box--partial': isPartiallySelected(category),
                }"
                aria-hidden="true"
              >
                <AppIcon
                  v-if="isFullySelected(category)"
                  icon="lucide:check"
                  class="selection-box-icon"
                />
                <span
                  v-else-if="isPartiallySelected(category)"
                  class="selection-box-dash"
                ></span>
              </span>
              <div class="category-copy">
                <span class="category-name">{{ category.name }}</span>
                <span v-if="category.meaning" class="category-meaning">
                  {{ category.meaning }}
                </span>
              </div>
            </label>

            <div class="category-right">
              <span class="category-count">
                {{ category.subcategories.length }} 个数据集
              </span>
              <button
                class="expand-btn"
                type="button"
                :aria-label="expandedCategoryIds.includes(category.categoryId) ? '收起' : '展开'"
                :title="expandedCategoryIds.includes(category.categoryId) ? '收起' : '展开'"
                @click="$emit('toggle-expanded', category.categoryId)"
              >
                <AppIcon
                  :icon="expandedCategoryIds.includes(category.categoryId) ? 'lucide:chevron-up' : 'lucide:chevron-down'"
                  class="expand-btn-icon"
                />
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
                class="selection-input"
                :checked="selectedDatasetIds.includes(dataset.datasetId)"
                @change="$emit('toggle-dataset', dataset.datasetId)"
              />
              <span
                class="selection-box"
                :class="{
                  'selection-box--checked': selectedDatasetIds.includes(dataset.datasetId),
                }"
                aria-hidden="true"
              >
                <AppIcon
                  v-if="selectedDatasetIds.includes(dataset.datasetId)"
                  icon="lucide:check"
                  class="selection-box-icon"
                />
              </span>
              <div class="dataset-copy">
                <span class="dataset-name">{{ dataset.name }}</span>
                <span class="dataset-description">
                  {{ dataset.shortDescription || "暂无数据集说明。" }}
                </span>
              </div>
            </label>
          </div>
        </article>
      </div>
    </template>

    <PageStateCard
      v-else-if="categories.length && status !== 'loading'"
      title="没有匹配的数据集"
      message="请尝试更换搜索词，或直接清空搜索。"
    />
  </SectionCard>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import type { DatasetCategoryViewModel } from "@/shared/types/dataset-types";
import type { SubmitDatasetCatalogStatus } from "@/modules/submission/composables/useSubmitDatasetCatalog";
import {
  getCategoryTheme,
  isCategoryFullySelected,
} from "@/modules/dataset/lib/dataset-utils";
import FormField from "@/shared/ui/forms/FormField.vue";
import InlineNotice from "@/shared/ui/feedback/InlineNotice.vue";
import PageStateCard from "@/shared/ui/feedback/PageStateCard.vue";
import SectionCard from "@/shared/ui/page/SectionCard.vue";
import UiButton from "@/shared/ui/actions/UiButton.vue";
import AppIcon from "@/shared/ui/branding/AppIcon.vue";

const props = defineProps<{
  categories: DatasetCategoryViewModel[];
  selectedDatasetIds: string[];
  expandedCategoryIds: string[];
  status: SubmitDatasetCatalogStatus;
  errorMessage?: string;
  selectionErrorMessage?: string;
}>();

defineEmits<{
  (event: "select-all"): void;
  (event: "clear-all"): void;
  (event: "toggle-category", categoryId: string): void;
  (event: "toggle-dataset", datasetId: string): void;
  (event: "toggle-expanded", categoryId: string): void;
  (event: "retry"): void;
}>();

const search = ref("");

const matchesSearch = (category: DatasetCategoryViewModel, keyword: string) => {
  if (!keyword) {
    return true;
  }

  const normalized = keyword.toLowerCase();
  const categoryMatched = [
    category.name,
    category.meaning ?? "",
    category.description ?? "",
  ].some((value) => value.toLowerCase().includes(normalized));

  if (categoryMatched) {
    return true;
  }

  return category.subcategories.some((dataset) =>
    [dataset.name, dataset.shortDescription ?? ""].some((value) =>
      value.toLowerCase().includes(normalized),
    ),
  );
};

const filteredCategories = computed(() => {
  const keyword = search.value.trim().toLowerCase();

  return props.categories
    .filter((category) => matchesSearch(category, keyword))
    .map((category) => ({
      ...category,
      subcategories: category.subcategories.filter((dataset) => {
        if (!keyword) {
          return true;
        }

        return [
          category.name,
          category.meaning ?? "",
          dataset.name,
          dataset.shortDescription ?? "",
        ].some((value) => value.toLowerCase().includes(keyword));
      }),
    }))
    .filter((category) => category.subcategories.length > 0);
});

const visibleDatasetCount = computed(() =>
  filteredCategories.value.reduce(
    (count, category) => count + category.subcategories.length,
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

const isPartiallySelected = (category: DatasetCategoryViewModel) => {
  const selectedCount = category.subcategories.filter((item) =>
    props.selectedDatasetIds.includes(item.datasetId),
  ).length;

  return selectedCount > 0 && selectedCount < category.subcategories.length;
};

const getCategoryBlockStyle = (categoryId: string) => {
  const theme = getCategoryTheme(categoryId);

  return {
    "--category-soft": theme.soft,
    "--category-border": theme.border,
    "--category-text": theme.text,
    "--category-gradient": theme.gradient,
    "--category-shadow": theme.shadow,
  };
};
</script>

<style scoped lang="scss">
.toolbar {
  display: grid;
  grid-template-columns: minmax(240px, 1.4fr) minmax(0, 1fr);
  gap: 0.85rem;
}

.toolbar-metrics {
  display: flex;
  flex-wrap: wrap;
  align-items: end;
  justify-content: flex-end;
  gap: 0.75rem;
  color: var(--color-text-muted);
  font-size: 0.9rem;
}

.status-list {
  display: flex;
  flex-direction: column;
  gap: 0.7rem;
}

.category-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.category-block {
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
  background: linear-gradient(180deg, var(--category-soft, #f8fafc), #ffffff 88%);
}

.category-main {
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: 0.8rem;
  min-width: 0;
}

.selection-input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.selection-box {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.15rem;
  height: 1.15rem;
  margin-top: 0.08rem;
  border-radius: 0.34rem;
  border: 1px solid rgba(148, 163, 184, 0.34);
  background: rgba(255, 255, 255, 0.96);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.82);
  transition: background var(--duration-fast) var(--ease-standard), border-color var(--duration-fast) var(--ease-standard), box-shadow var(--duration-fast) var(--ease-standard);
  flex-shrink: 0;
}

.selection-box--checked,
.selection-box--partial {
  border-color: rgba(37, 99, 235, 0.92);
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.98), rgba(59, 130, 246, 0.94));
  box-shadow: 0 8px 18px -14px rgba(37, 99, 235, 0.74);
}

.selection-box-icon {
  width: 0.82rem;
  height: 0.82rem;
  color: #ffffff;
}

.selection-box-dash {
  width: 0.56rem;
  height: 0.12rem;
  border-radius: 999px;
  background: #ffffff;
}

.category-copy {
  display: flex;
  flex-direction: column;
  gap: 0.24rem;
}

.category-name {
  color: var(--color-text-dark);
  font-weight: 700;
}

.category-meaning {
  color: var(--category-text, #475569);
  font-size: 0.9rem;
}

.category-right {
  display: inline-flex;
  align-items: center;
  gap: 0.75rem;
}

.category-count {
  color: var(--color-text-subtle);
  font-size: 0.88rem;
}

.expand-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.35rem;
  height: 2.35rem;
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.92);
  color: var(--category-text, #334155);
  cursor: pointer;
  box-shadow: 0 10px 20px -18px rgba(15, 23, 42, 0.32);
  transition: transform var(--duration-fast) var(--ease-standard), box-shadow var(--duration-fast) var(--ease-standard), background var(--duration-fast) var(--ease-standard);
}

.expand-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 12px 22px -18px rgba(15, 23, 42, 0.36);
}

.expand-btn-icon {
  width: 1rem;
  height: 1rem;
}

.dataset-list {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
  padding: 0 1.05rem 1rem;
}

.dataset-item {
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: 0.7rem;
  padding: 0.85rem 0.9rem;
  border-radius: 1rem;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(148, 163, 184, 0.14);
}

.dataset-copy {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 0.28rem;
}

.dataset-name {
  color: var(--color-text-dark);
  font-weight: 600;
}

.dataset-description {
  color: var(--color-text-subtle);
  line-height: 1.65;
}

@media (max-width: 768px) {
  .toolbar {
    grid-template-columns: 1fr;
  }

  .toolbar-metrics,
  .category-right {
    width: 100%;
    justify-content: flex-start;
  }

  .category-row {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>