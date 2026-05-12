<template>
  <div class="content dataset-page layout-page-shell">
    <PageHero
      :title="t('dataset.pages.catalog.title')"
      :description="t('dataset.pages.catalog.description')"
    />

    <PageStatePanel
      v-if="loading && !loaded"
      :title="t('dataset.pages.catalog.loadingTitle')"
      :message="t('dataset.pages.catalog.loadingMessage')"
      :loading="true"
    />

    <PageStatePanel
      v-else-if="error && !enabledCategories.length"
      :title="t('dataset.pages.catalog.loadFailedTitle')"
      :message="error"
      :action-text="t('dataset.pages.catalog.reloadAction')"
      @action="reloadCatalog"
    />

    <PageStatePanel
      v-else-if="!activeCategory"
      :title="t('dataset.pages.catalog.emptyTitle')"
      :message="t('dataset.pages.catalog.emptyMessage')"
    />

    <template v-else>
      <DatasetFilterBar
        :categories="enabledCategories"
        :active-category-id="activeCategoryId"
        :search="search"
        :sort-key="sortKey"
        @select-category="setActiveCategory"
        @update:search="search = $event"
        @update:sort-key="sortKey = $event"
        @clear-search="search = ''"
      />

      <div v-if="filteredCategory" class="section-list">
        <DatasetCategorySection
          :key="`${filteredCategory.categoryId}-${sortKey}-${search}`"
          :category="filteredCategory"
        />
      </div>

      <PageStatePanel
        v-else
        :title="t('dataset.pages.catalog.noMatchesTitle')"
        :message="t('dataset.pages.catalog.noMatchesMessage')"
      />
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import { storeToRefs } from "pinia";
import DatasetCategorySection from "@/modules/dataset/components/DatasetCategorySection.vue";
import DatasetFilterBar from "@/modules/dataset/components/DatasetFilterBar.vue";
import {
  buildDatasetCatalogView,
  type DatasetCatalogSortKey,
} from "@/modules/dataset/model/dataset-catalog-view";
import { useDatasetCatalogStore } from "@/modules/dataset/stores/datasetCatalogStore";
import PageHero from "@/shared/ui/page/PageHero.vue";
import PageStatePanel from "@/shared/ui/feedback/PageStatePanel.vue";

const { t } = useI18n();
const datasetCatalogStore = useDatasetCatalogStore();
const {
  enabledCategories,
  activeCategory,
  activeCategoryId,
  loading,
  loaded,
  error,
} = storeToRefs(datasetCatalogStore);

const search = ref("");
const sortKey = ref<DatasetCatalogSortKey>("default");

const filteredCategory = computed(() => {
  if (!activeCategory.value) {
    return null;
  }

  return buildDatasetCatalogView(
    activeCategory.value,
    search.value,
    sortKey.value,
  ).category;
});

const reloadCatalog = async () => {
  await datasetCatalogStore.fetchCatalog(true);
};

const setActiveCategory = (categoryId: string) => {
  datasetCatalogStore.setActiveCategory(categoryId);
};

onMounted(async () => {
  await datasetCatalogStore.fetchCatalog();
});
</script>

<style scoped lang="scss">
.dataset-page {
  padding-bottom: 2.5rem;
}

.section-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
</style>
