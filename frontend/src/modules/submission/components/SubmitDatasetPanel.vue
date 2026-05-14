<template>
  <SectionBlock
    :title="t('submission.dataset.title')"
    :description="t('submission.dataset.description')"
  >
    <template #actions>
      <UiButton
        variant="secondary"
        size="sm"
        :disabled="!categories.length"
        @click="$emit('select-all')"
      >
        {{ t("submission.actions.selectAll") }}
      </UiButton>
      <UiButton
        variant="secondary"
        size="sm"
        :disabled="!selectedDatasetIds.length"
        @click="$emit('clear-all')"
      >
        {{ t("submission.actions.clear") }}
      </UiButton>
    </template>

    <div class="toolbar">
      <FormField
        :label="t('submission.dataset.searchLabel')"
        :model-value="search"
        type="search"
        :placeholder="t('submission.dataset.searchPlaceholder')"
        leading-icon="app:action.search"
        @update:model-value="search = $event.trim()"
      />

      <div class="toolbar-metrics">
        <span>{{ t("submission.dataset.selectedRiskDomains", { count: selectedCategoryCount }) }}</span>
        <span>{{ t("submission.dataset.selectedDatasets", { count: selectedDatasetIds.length }) }}</span>
        <span>{{ t("submission.dataset.currentResults", { count: visibleDatasetCount }) }}</span>
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
        :message="t('submission.dataset.refreshing')"
      />
      <PageStatePanel
        v-if="status === 'loading' && !categories.length"
        :title="t('submission.dataset.loadingTitle')"
        :message="t('submission.dataset.loadingMessage')"
        :loading="true"
      />
      <PageStatePanel
        v-else-if="status === 'error' && !categories.length"
        :title="t('submission.dataset.loadFailedTitle')"
        :message="errorMessage || t('submission.dataset.retrySubmit')"
        :action-text="t('common.actions.retry')"
        action-variant="secondary"
        @action="$emit('retry')"
      />
      <PageStatePanel
        v-else-if="status === 'empty'"
        :title="t('submission.dataset.emptyTitle')"
        :message="t('submission.dataset.emptyMessage')"
      />
      <InlineNotice
        v-else-if="status === 'error'"
        tone="danger"
        :message="errorMessage || t('submission.dataset.refreshFailed')"
      >
        <template #actions>
          <UiButton variant="text" size="sm" @click="$emit('retry')">
            {{ t("submission.actions.reload") }}
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
      :title="t('submission.dataset.noMatchesTitle')"
      :message="t('submission.dataset.clearSearchMessage')"
    />
  </SectionBlock>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { useI18n } from "vue-i18n";
import SubmitDatasetCategoryList from "@/modules/submission/components/SubmitDatasetCategoryList.vue";
import type { DatasetCategory } from "@/shared/types/dataset-types";
import type { SubmitDatasetCatalogStatus } from "@/modules/submission/composables/useSubmitDatasetCatalog";
import FormField from "@/shared/ui/forms/FormField.vue";
import InlineNotice from "@/shared/ui/feedback/InlineNotice.vue";
import PageStatePanel from "@/shared/ui/feedback/PageStatePanel.vue";
import SectionBlock from "@/shared/ui/page/SectionBlock.vue";
import UiButton from "@/shared/ui/actions/UiButton.vue";

const props = defineProps<{
  categories: DatasetCategory[];
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
const { t } = useI18n();

const matchesSearch = (category: DatasetCategory, keyword: string) => {
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
