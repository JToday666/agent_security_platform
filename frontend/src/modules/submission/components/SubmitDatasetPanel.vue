<template>
  <SectionBlock
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
      <PageStatePanel
        v-if="status === 'loading' && !categories.length"
        title="正在加载数据集"
        message="请稍候。"
        :loading="true"
      />
      <PageStatePanel
        v-else-if="status === 'error' && !categories.length"
        title="数据集目录加载失败"
        :message="errorMessage || '请重试后继续提交。'"
        action-text="重试"
        action-variant="secondary"
        @action="$emit('retry')"
      />
      <PageStatePanel
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
      <SubmitDatasetCategoryList
        :categories="filteredCategories"
        :selected-dataset-ids="selectedDatasetIds"
        :expanded-category-ids="expandedCategoryIds"
        @toggle-category="$emit('toggle-category', $event)"
        @toggle-dataset="$emit('toggle-dataset', $event)"
        @toggle-expanded="$emit('toggle-expanded', $event)"
      />
    </template>

    <PageStatePanel
      v-else-if="categories.length && status !== 'loading'"
      title="没有匹配的数据集"
      message="请尝试更换搜索词，或直接清空搜索。"
    />
  </SectionBlock>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import SubmitDatasetCategoryList from "@/modules/submission/components/SubmitDatasetCategoryList.vue";
import type { DatasetCategoryViewModel } from "@/shared/types/dataset-types";
import type { SubmitDatasetCatalogStatus } from "@/modules/submission/composables/useSubmitDatasetCatalog";
import FormField from "@/shared/ui/forms/FormField.vue";
import InlineNotice from "@/shared/ui/feedback/InlineNotice.vue";
import PageStatePanel from "@/shared/ui/feedback/PageStatePanel.vue";
import SectionBlock from "@/shared/ui/page/SectionBlock.vue";
import UiButton from "@/shared/ui/actions/UiButton.vue";

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
</script>

<style scoped lang="scss">
.toolbar {
  display: grid;
  grid-template-columns: minmax(240px, 1.4fr) minmax(0, 1fr);
  gap: 0.85rem;
  min-width: 0;
}

.toolbar-metrics {
  display: flex;
  flex-wrap: wrap;
  align-items: end;
  justify-content: flex-end;
  gap: 0.75rem;
  min-width: 0;
  color: var(--color-text-muted);
  font-size: 0.9rem;
}

.toolbar-metrics > * {
  min-width: 0;
}

.status-list {
  display: flex;
  flex-direction: column;
  gap: 0.7rem;
}

@media (max-width: 768px) {
  .toolbar {
    grid-template-columns: 1fr;
  }

  .toolbar-metrics {
    width: 100%;
    justify-content: flex-start;
  }
}
</style>
