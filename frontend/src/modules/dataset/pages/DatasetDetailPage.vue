<template>
  <div class="content detail-page layout-page-shell">
    <PageHero
      :title="detail?.name || t('dataset.pages.detail.titleFallback')"
      :description="
        detail?.shortDescription || t('dataset.pages.detail.descriptionFallback')
      "
    >
      <template #actions>
        <div class="hero-actions">
          <UiButton
            :to="RouteLocation.datasetList"
            variant="secondary"
            leading-icon="app:action.back"
          >
            {{ t("dataset.pages.detail.backToCatalog") }}
          </UiButton>
          <UiButton
            v-if="detail"
            variant="primary"
            leading-icon="app:action.submitEvaluation"
            @click="handleSubmitClick"
          >
            {{
              isLogin
                ? t("dataset.pages.detail.submitWithDataset")
                : t("dataset.pages.detail.loginToEvaluateDataset")
            }}
          </UiButton>
        </div>
      </template>
    </PageHero>

    <PageStatePanel
      v-if="loading"
      :title="t('dataset.pages.detail.loadingTitle')"
      :message="t('dataset.pages.detail.loadingMessage')"
      :loading="true"
    />

    <PageStatePanel
      v-else-if="error"
      :title="
        notFound
          ? t('dataset.pages.detail.notFoundTitle')
          : t('dataset.pages.detail.detailLoadFailedTitle')
      "
      :message="error"
      :action-text="t('dataset.pages.detail.retryAction')"
      @action="loadDetail"
    />

    <div v-else-if="detail" class="detail-stack layout-page-stack">
      <DatasetMetaBar
        :category-name="detail.category.name"
        :category-meaning="
          detail.category.meaning || t('dataset.fallback.currentRiskDomain')
        "
        :sample-count="formatSampleCount(detail.sampleCount ?? undefined)"
        :updated-at="formatDateLabel(detail.updatedAt ?? undefined)"
      />

      <SectionBlock :title="t('dataset.pages.detail.sections.details')">
        <p class="long-copy">
          {{ detail.fullDescription || t("dataset.pages.detail.fullDescriptionFallback") }}
        </p>
      </SectionBlock>

      <div class="grid-layout layout-two-column">
        <SectionBlock :title="t('dataset.pages.detail.sections.highlights')">
          <ul class="bullet-list">
            <li v-for="item in detail.highlights" :key="item">{{ item }}</li>
          </ul>
        </SectionBlock>

        <SectionBlock :title="t('dataset.pages.detail.sections.scenarios')">
          <ul class="bullet-list">
            <li v-for="item in detail.scenarios" :key="item">{{ item }}</li>
          </ul>
        </SectionBlock>
      </div>

      <DatasetResourcesList :resources="detail.resources" />

      <SectionBlock :title="t('dataset.pages.detail.sections.media')">
        <DatasetMediaGallery :media="detail.media" />
      </SectionBlock>

      <SectionBlock
        class="cta-section"
        :title="t('dataset.pages.detail.ctaTitle')"
        :description="t('dataset.pages.detail.ctaDescription')"
      >
        <template #actions>
          <UiButton
            variant="primary"
            leading-icon="app:action.submitEvaluation"
            @click="handleSubmitClick"
          >
            {{
              isLogin
                ? t("dataset.pages.detail.submitWithDataset")
                : t("dataset.pages.detail.loginToEvaluateDataset")
            }}
          </UiButton>
        </template>
      </SectionBlock>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
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

const { t } = useI18n();
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

.cta-section :deep(.section-block__head) {
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.cta-section :deep(.section-block__copy) {
  max-width: 34rem;
}

.cta-section :deep(.section-block__actions) {
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
