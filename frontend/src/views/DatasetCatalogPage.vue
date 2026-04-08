<template>
  <div class="content dataset-page layout-page-shell">
    <PageHeroCard
      eyebrow="评测目录"
      title="风险评测目录"
      description="按风险域浏览当前可用评测项，支持筛选、查看详情，并快速发起评测。"
      :chips="heroChips"
    />

    <p v-if="restoredFilterNotice" class="notice-banner ui-surface-white">
      已恢复上次筛选状态。
    </p>

    <div v-if="loading && !loaded" class="state-card layout-state-card ui-surface-white">
      <h2>正在加载目录</h2>
      <p>稍等片刻，系统正在同步最新风险评测目录。</p>
    </div>

    <div
      v-else-if="error && !enabledCategories.length"
      class="state-card layout-state-card ui-surface-white"
    >
      <h2>目录加载失败</h2>
      <p>{{ error }}</p>
      <button
        class="retry-btn layout-retry-btn ui-btn ui-btn-pill ui-btn-gradient ui-btn-hover-lift"
        @click="reloadCatalog"
      >
        重新加载
      </button>
    </div>

    <template v-else>
      <DatasetFilterBar
        :categories="enabledCategories"
        :selected-category-ids="selectedCategoryIds"
        :visible-dataset-count="visibleDatasetCount"
        @select-all="selectAllCategories"
        @clear-all="clearAllCategories"
        @toggle-category="toggleCategorySelection"
      />

      <div v-if="visibleCategories.length" class="section-list">
        <DatasetCategorySection
          v-for="category in visibleCategories"
          :key="category.categoryId"
          :category="category"
        />
      </div>

      <div v-else class="state-card layout-state-card ui-surface-white">
        <h2>当前没有可显示的评测项</h2>
        <p>你已清空全部风险域筛选，可一键恢复全选继续浏览。</p>
        <button
          class="retry-btn layout-retry-btn ui-btn ui-btn-pill ui-btn-gradient"
          @click="selectAllCategories"
        >
          恢复全选
        </button>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from "vue";
import { storeToRefs } from "pinia";
import PageHeroCard from "@/components/common/PageHeroCard.vue";
import DatasetFilterBar from "@/components/dataset/DatasetFilterBar.vue";
import DatasetCategorySection from "@/components/dataset/DatasetCategorySection.vue";
import { useDatasetCatalogStore } from "@/store/DatasetCatalogStore";

// 列表页只消费统一目录 store，所有筛选都在前端本地完成。
const datasetCatalogStore = useDatasetCatalogStore();
const {
  enabledCategories,
  visibleCategories,
  selectedCategoryIds,
  loading,
  loaded,
  error,
  restoredFilterNotice,
} = storeToRefs(datasetCatalogStore);

const totalDatasetCount = computed(() =>
  enabledCategories.value.reduce(
    (sum, category) => sum + category.subcategories.length,
    0,
  ),
);

const visibleDatasetCount = computed(() =>
  visibleCategories.value.reduce(
    (sum, category) => sum + category.subcategories.length,
    0,
  ),
);

const heroChips = computed(() => [
  {
    label: "全部风险域",
    value: `${enabledCategories.value.length} 个`,
  },
  {
    label: "全部评测项",
    value: `${totalDatasetCount.value} 个`,
  },
  {
    label: "当前可见评测项",
    value: `${visibleDatasetCount.value} 个`,
  },
]);

const reloadCatalog = async () => {
  await datasetCatalogStore.fetchCatalog(true);
};

const selectAllCategories = () => {
  datasetCatalogStore.selectAllCategories();
};

const clearAllCategories = () => {
  datasetCatalogStore.clearAllCategories();
};

const toggleCategorySelection = (categoryId: string) => {
  datasetCatalogStore.toggleCategorySelection(categoryId);
};

onMounted(async () => {
  await datasetCatalogStore.fetchCatalog();
});
</script>

<style scoped>
.dataset-page {
  padding-bottom: 2.5rem;
}

.notice-banner {
  margin: -0.4rem 0 1rem;
  padding: 0.95rem 1rem;
  border-radius: 1rem;
  color: #1d4ed8;
  font-weight: 600;
}

.section-list {
  display: flex;
  flex-direction: column;
  gap: 0;
}
</style>
