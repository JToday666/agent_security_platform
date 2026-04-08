<template>
  <div class="content detail-page layout-page-shell">
    <PageHeroCard
      :eyebrow="detail?.category.name || '评测项详情'"
      :title="detail?.name || '评测项详情'"
      :description="detail?.shortDescription || '查看该评测项的详细说明、评测重点、典型场景与相关示例资源。'"
      :chips="heroChips"
    >
      <template #actions>
        <button class="back-btn ui-btn ui-btn-pill" type="button" @click="goBack">
          返回评测目录
        </button>
      </template>
    </PageHeroCard>

    <div v-if="loading" class="state-card layout-state-card ui-surface-white">
      <h2>正在加载详情</h2>
      <p>系统正在获取该评测项的说明、媒体资源和评测信息。</p>
    </div>

    <div v-else-if="error" class="state-card layout-state-card ui-surface-white">
      <h2>{{ notFound ? "评测项不存在" : "详情加载失败" }}</h2>
      <p>{{ error }}</p>
      <button class="retry-btn layout-retry-btn ui-btn ui-btn-pill ui-btn-gradient" @click="loadDetail">
        重试
      </button>
    </div>

    <template v-else-if="detail">
      <section class="section-card layout-section-card ui-surface-white">
        <h2>详细说明</h2>
        <p class="long-copy">{{ detail.fullDescription }}</p>
      </section>

      <div class="grid-layout layout-two-column">
        <section class="section-card layout-section-card ui-surface-white">
          <h2>评测重点</h2>
          <ul class="bullet-list">
            <li v-for="item in detail.highlights" :key="item">{{ item }}</li>
          </ul>
        </section>

        <section class="section-card layout-section-card ui-surface-white">
          <h2>典型场景</h2>
          <ul class="bullet-list">
            <li v-for="item in detail.scenarios" :key="item">{{ item }}</li>
          </ul>
        </section>
      </div>

      <section class="section-card layout-section-card ui-surface-white">
        <h2>媒体与运行效果</h2>
        <p class="section-note">
          可查看该评测项的样例图片和演示视频；若资源暂时无法加载，页面会提示当前不可用。
        </p>
        <DatasetMediaGallery :media="detail.media" />
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import PageHeroCard from "@/components/common/PageHeroCard.vue";
import DatasetMediaGallery from "@/components/dataset/DatasetMediaGallery.vue";
import { RouteLocation } from "@/router/RouteNames";
import type { DatasetDetail as DatasetDetailType } from "@/types/DatasetTypes";
import {
  formatSampleCount,
} from "@/utils/common";
import { useDatasetCatalogStore } from "@/store/DatasetCatalogStore";

const route = useRoute();
const router = useRouter();
const datasetCatalogStore = useDatasetCatalogStore();

const detail = ref<DatasetDetailType | null>(null);
const loading = ref(false);
const error = ref("");
const notFound = ref(false);

// 详情页只接受规范化的 datasetId 参数。
const datasetId = computed(() => String(route.params.datasetId ?? ""));

const heroChips = computed(() => [
  {
    label: "样本数",
    value: formatSampleCount(detail.value?.sampleCount),
  },
  {
    label: "评测重点",
    value: `${detail.value?.highlights.length ?? 0} 条`,
  },
  {
    label: "典型场景",
    value: `${detail.value?.scenarios.length ?? 0} 条`,
  },
]);

// 每次路由参数变化时重新拉取详情，保证直接切换详情页时内容同步。
const loadDetail = async () => {
  loading.value = true;
  error.value = "";
  notFound.value = false;

  try {
    const result = await datasetCatalogStore.fetchDatasetDetailById(
      datasetId.value,
      true,
    );

    if (!result.detail) {
      detail.value = null;
      notFound.value = result.notFound;
      error.value = result.errorMessage;
      return;
    }

    detail.value = result.detail;
  } finally {
    loading.value = false;
  }
};

const goBack = () => {
  if (window.history.length > 1) {
    router.back();
    return;
  }

  router.push(RouteLocation.datasetList);
};

watch(datasetId, async () => {
  await loadDetail();
});

onMounted(async () => {
  await loadDetail();
});
</script>

<style scoped>
.detail-page {
  padding-bottom: 2.5rem;
}

.back-btn {
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(203, 213, 225, 0.8);
  color: #334155;
  padding: 0.85rem 1.15rem;
}

.section-card {
  margin-top: 1rem;
}

.long-copy,
.section-note {
  margin: 0.85rem 0 0;
  color: #475569;
  line-height: 1.85;
}

.grid-layout {
  margin-top: 1rem;
}

.bullet-list {
  margin: 0.85rem 0 0;
  padding-left: 1.1rem;
  color: #475569;
  line-height: 1.85;
}
</style>
