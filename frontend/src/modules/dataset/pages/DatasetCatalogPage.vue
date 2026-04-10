<template>
  <div class="content dataset-page layout-page-shell">
    <PageHeroCard
      eyebrow="评测目录"
      title="风险评测目录"
      description="默认展示首个风险域的评测项，点击风险域标签即可切换查看其他方向。"
      :chips="heroChips"
    />

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

    <div v-else-if="!activeCategory" class="state-card layout-state-card ui-surface-white">
      <h2>当前暂无可用评测项</h2>
      <p>系统暂未返回可展示的风险域或评测项，请稍后重试。</p>
    </div>

    <template v-else>
      <DatasetFilterBar
        :categories="enabledCategories"
        :active-category-id="activeCategoryId"
        @select-category="setActiveCategory"
      />

      <div class="section-list">
        <DatasetCategorySection
          :key="activeCategory.categoryId"
          :category="activeCategory"
        />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from "vue";
import { storeToRefs } from "pinia";
import PageHeroCard from "@/shared/ui/PageHeroCard.vue";
import DatasetFilterBar from "@/modules/dataset/components/DatasetFilterBar.vue";
import DatasetCategorySection from "@/modules/dataset/components/DatasetCategorySection.vue";
import { useDatasetCatalogStore } from "@/modules/dataset/stores/DatasetCatalogStore";

// 目录页只消费统一目录 store，风险域切换保持为前端单选状态。
const datasetCatalogStore = useDatasetCatalogStore();
const {
  enabledCategories,
  activeCategory,
  activeCategoryId,
  loading,
  loaded,
  error,
} = storeToRefs(datasetCatalogStore);

const totalDatasetCount = computed(() =>
  enabledCategories.value.reduce(
    (sum, category) => sum + category.subcategories.length,
    0,
  ),
);

const heroChips = computed(() => [
  {
    label: "风险域",
    value: `${enabledCategories.value.length} 个`,
  },
  {
    label: "评测项总数",
    value: `${totalDatasetCount.value} 个`,
  },
  {
    label: "当前风险域",
    value: activeCategory.value?.name ?? "暂无",
  },
]);

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

<style scoped>
.dataset-page {
  padding-bottom: 2.5rem;
}

.section-list {
  display: flex;
  flex-direction: column;
  gap: 0;
}
</style>
