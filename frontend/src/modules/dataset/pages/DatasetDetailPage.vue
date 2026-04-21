<template>
  <div class="content detail-page layout-page-shell">
    <PageHero
      :title="detail?.name || '数据集详情'"
      :description="detail?.shortDescription || '查看该数据集的说明、重点、资源与样例。'"
    >
      <template #actions>
        <div class="hero-actions">
          <UiButton
            :to="RouteLocation.datasetList"
            variant="secondary"
            leading-icon="lucide:arrow-left"
          >
            返回数据集目录
          </UiButton>
          <UiButton
            v-if="detail"
            variant="primary"
            leading-icon="lucide:file-plus-2"
            @click="handleSubmitClick"
          >
            {{ isLogin ? "使用此数据集发起评测" : "登录后评测此数据集" }}
          </UiButton>
        </div>
      </template>
    </PageHero>

    <PageStatePanel
      v-if="loading"
      title="正在加载详情"
      message="请稍候。"
      :loading="true"
    />

    <PageStatePanel
      v-else-if="error"
      :title="notFound ? '评测项不存在' : '详情加载失败'"
      :message="error"
      action-text="重试"
      @action="loadDetail"
    />

    <div v-else-if="detail" class="detail-stack layout-page-stack">
      <DatasetMetaBar
        :category-name="detail.category.name"
        :category-meaning="detail.category.meaning || '当前风险域'"
        :sample-count="formatSampleCount(detail.sampleCount ?? undefined)"
        :updated-at="formatDateLabel(detail.updatedAt ?? undefined)"
      />

      <SectionBlock title="详细说明">
        <p class="long-copy">{{ detail.fullDescription || "暂无详细说明。" }}</p>
      </SectionBlock>

      <div class="grid-layout layout-two-column">
        <SectionBlock title="评测重点">
          <ul class="bullet-list">
            <li v-for="item in detail.highlights" :key="item">{{ item }}</li>
          </ul>
        </SectionBlock>

        <SectionBlock title="典型场景">
          <ul class="bullet-list">
            <li v-for="item in detail.scenarios" :key="item">{{ item }}</li>
          </ul>
        </SectionBlock>
      </div>

      <DatasetResourcesList :resources="detail.resources" />

      <SectionBlock title="媒体资料" surface="panel">
        <DatasetMediaGallery :media="detail.media" />
      </SectionBlock>

      <SectionBlock
        class="cta-card"
        title="准备发起评测"
        description="当前数据集选定后，可直接进入提交页继续配置智能体接入方式与运行参数。"
        surface="panel"
      >
        <template #actions>
          <UiButton
            variant="primary"
            leading-icon="lucide:file-plus-2"
            @click="handleSubmitClick"
          >
            {{ isLogin ? "使用此数据集发起评测" : "登录后评测此数据集" }}
          </UiButton>
        </template>
      </SectionBlock>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { storeToRefs } from "pinia";
import { useRoute, useRouter } from "vue-router";
import { RouteLocation } from "@/app/router/route-names";
import { useUserStore } from "@/modules/account/stores/userStore";
import DatasetMediaGallery from "@/modules/dataset/components/DatasetMediaGallery.vue";
import DatasetMetaBar from "@/modules/dataset/components/DatasetMetaBar.vue";
import DatasetResourcesList from "@/modules/dataset/components/DatasetResourcesList.vue";
import {
  formatDateLabel,
  formatSampleCount,
} from "@/modules/dataset/lib/dataset-utils";
import { useDatasetCatalogStore } from "@/modules/dataset/stores/datasetCatalogStore";
import type { DatasetDetail as DatasetDetailType } from "@/shared/types/dataset-types";
import UiButton from "@/shared/ui/actions/UiButton.vue";
import PageStatePanel from "@/shared/ui/feedback/PageStatePanel.vue";
import PageHero from "@/shared/ui/page/PageHero.vue";
import SectionBlock from "@/shared/ui/page/SectionBlock.vue";

const route = useRoute();
const router = useRouter();
const datasetCatalogStore = useDatasetCatalogStore();
const userStore = useUserStore();
const { isLogin } = storeToRefs(userStore);

const detail = ref<DatasetDetailType | null>(null);
const loading = ref(false);
const error = ref("");
const notFound = ref(false);

const datasetId = computed(() => String(route.params.datasetId ?? ""));

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

const handleSubmitClick = () => {
  if (!detail.value) {
    return;
  }

  if (!isLogin.value) {
    userStore.openLoginDialog();
    return;
  }

  void router.push({
    ...RouteLocation.agentSubmit,
    query: {
      datasetIds: detail.value.datasetId,
    },
  });
};

watch(datasetId, async () => {
  await loadDetail();
});

onMounted(async () => {
  await loadDetail();
});
</script>

<style scoped lang="scss">
.detail-page {
  padding-bottom: 2.5rem;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.long-copy {
  margin: 0;
  color: var(--color-text-muted);
  line-height: 1.85;
}

.bullet-list {
  margin: 0;
  padding-left: 1.1rem;
  color: var(--color-text-muted);
  line-height: 1.85;
}

.cta-card :deep(.section-block__head) {
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.cta-card :deep(.section-block__copy) {
  max-width: 34rem;
}

.cta-card :deep(.section-block__actions) {
  width: 100%;
  justify-content: center;
}

@media (max-width: 768px) {
  .hero-actions {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
