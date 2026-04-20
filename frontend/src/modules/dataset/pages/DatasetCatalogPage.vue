<template>
  <div class="content dataset-page layout-page-shell">
    <PageHeroCard
      title="数据集目录"
      description="按风险域浏览可用数据集，并查看说明。"
      density="default"
      tone="showcase"
    />

    <PageStateCard
      v-if="loading && !loaded"
      title="正在加载目录"
      message="请稍候。"
      :loading="true"
    />

    <PageStateCard
      v-else-if="error && !enabledCategories.length"
      title="目录加载失败"
      :message="error"
      action-text="重新加载"
      @action="reloadCatalog"
    />

    <PageStateCard
      v-else-if="!activeCategory"
      title="当前暂无可用数据集"
      message="请稍后重试。"
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

      <PageStateCard
        v-else
        title="没有找到匹配的数据集"
        message="请尝试更换关键词或切换风险域。"
      />
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { storeToRefs } from "pinia";
import DatasetCategorySection from "@/modules/dataset/components/DatasetCategorySection.vue";
import DatasetFilterBar from "@/modules/dataset/components/DatasetFilterBar.vue";
import {
  buildDatasetCatalogView,
  type DatasetCatalogSortKey,
} from "@/modules/dataset/model/dataset-catalog-view";
import { useDatasetCatalogStore } from "@/modules/dataset/stores/datasetCatalogStore";
import PageHeroCard from "@/shared/ui/page/PageHeroCard.vue";
import PageStateCard from "@/shared/ui/feedback/PageStateCard.vue";

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