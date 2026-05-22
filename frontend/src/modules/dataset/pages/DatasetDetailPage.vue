<template>
  <div class="content detail-page layout-page-shell">
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

    <div v-else-if="detail" class="detail-stack" :style="detailThemeStyle">
      <UiButton
        :to="RouteLocation.datasetList"
        variant="text"
        leading-icon="app:action.back"
      >
        {{ t("dataset.pages.detail.backToCatalog") }}
      </UiButton>

      <header class="detail-summary">
        <div class="detail-summary__copy">
          <span class="category-badge">{{ detail.category.name }}</span>
          <div class="detail-summary__title-row">
            <h1>{{ detail.name }}</h1>
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
          </div>
          <p>
            {{
              detail.shortDescription ||
              t("dataset.pages.detail.descriptionFallback")
            }}
          </p>
          <div class="detail-summary__meta">
            <span>
              {{ t("dataset.labels.sampleCount") }}
              <strong>{{ formatSampleCount(detail.sampleCount ?? undefined) }}</strong>
            </span>
            <span>
              {{ t("dataset.labels.updatedAt") }}
              <strong>{{ formatDateLabel(detail.updatedAt ?? undefined) }}</strong>
            </span>
          </div>
        </div>
      </header>

      <div class="detail-layout">
        <main class="detail-main" :aria-label="t('dataset.pages.detail.mainLabel')">
          <section class="detail-section">
            <h2>{{ t("dataset.pages.detail.sections.details") }}</h2>
            <p class="long-copy">
              {{
                detail.fullDescription ||
                t("dataset.pages.detail.fullDescriptionFallback")
              }}
            </p>
          </section>

          <section class="detail-section">
            <h2>{{ t("dataset.pages.detail.sections.highlights") }}</h2>
            <ol v-if="detail.highlights.length" class="numbered-list">
              <li v-for="item in detail.highlights" :key="item">
                <span>{{ item }}</span>
              </li>
            </ol>
            <p v-else class="empty-copy">
              {{ t("dataset.pages.detail.emptyHighlights") }}
            </p>
          </section>

          <section class="detail-section">
            <h2>{{ t("dataset.pages.detail.sections.scenarios") }}</h2>
            <ol v-if="detail.scenarios.length" class="numbered-list">
              <li v-for="item in detail.scenarios" :key="item">
                <span>{{ item }}</span>
              </li>
            </ol>
            <p v-else class="empty-copy">
              {{ t("dataset.pages.detail.emptyScenarios") }}
            </p>
          </section>

          <DatasetAssetsSection :resources="detail.resources" :media="detail.media" />
        </main>

        <aside class="detail-aside" :aria-label="t('dataset.pages.detail.sideLabel')">
          <section class="side-panel side-facts">
            <h2>{{ t("dataset.pages.detail.sideInfoTitle") }}</h2>
            <dl>
              <div>
                <dt>{{ t("dataset.labels.riskDomain") }}</dt>
                <dd>{{ detail.category.name }}</dd>
              </div>
              <div>
                <dt>{{ t("dataset.labels.sampleCount") }}</dt>
                <dd>{{ formatSampleCount(detail.sampleCount ?? undefined) }}</dd>
              </div>
              <div>
                <dt>{{ t("dataset.labels.updatedAt") }}</dt>
                <dd>{{ formatDateLabel(detail.updatedAt ?? undefined) }}</dd>
              </div>
            </dl>
          </section>

          <section class="side-panel side-actions">
            <h2>{{ t("dataset.pages.detail.sideActionTitle") }}</h2>
            <UiButton
              variant="primary"
              block
              leading-icon="app:action.submitEvaluation"
              @click="handleSubmitClick"
            >
              {{
                isLogin
                  ? t("dataset.pages.detail.submitWithDataset")
                  : t("dataset.pages.detail.loginToEvaluateDataset")
              }}
            </UiButton>
            <UiButton
              :to="RouteLocation.datasetList"
              variant="secondary"
              block
              leading-icon="app:action.back"
            >
              {{ t("dataset.pages.detail.backToCatalog") }}
            </UiButton>
          </section>

          <section v-if="sameRiskDatasets.length" class="side-panel side-related">
            <h2>{{ t("dataset.pages.detail.sameRiskTitle") }}</h2>
            <div class="related-list">
              <UiButton
                v-for="dataset in sameRiskDatasets"
                :key="dataset.datasetId"
                :to="RouteLocation.datasetDetail(dataset.datasetId)"
                variant="text"
                size="sm"
              >
                {{ dataset.name }}
              </UiButton>
            </div>
          </section>
        </aside>
      </div>
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
import DatasetAssetsSection from "@/modules/dataset/components/DatasetAssetsSection.vue";
import {
  formatDateLabel,
  formatSampleCount,
  getCategoryTheme,
} from "@/modules/dataset/lib/dataset-utils";
import { useDatasetCatalogStore } from "@/modules/dataset/stores/datasetCatalogStore";
import type {
  DatasetDetail as DatasetDetailType,
  DatasetSubcategory,
} from "@/shared/types/dataset-types";
import UiButton from "@/shared/ui/actions/UiButton.vue";
import PageStatePanel from "@/shared/ui/feedback/PageStatePanel.vue";

const { t } = useI18n();
const route = useRoute();
const router = useRouter();
const datasetCatalogStore = useDatasetCatalogStore();
const userStore = useUserStore();
const { isLogin } = storeToRefs(userStore);
const { enabledCategories } = storeToRefs(datasetCatalogStore);

const detail = ref<DatasetDetailType | null>(null);
const loading = ref(false);
const error = ref("");
const notFound = ref(false);

const datasetId = computed(() => String(route.params.datasetId ?? ""));

const detailThemeStyle = computed(() => {
  const theme = getCategoryTheme(detail.value?.category.categoryId ?? "");

  return {
    "--category-accent": theme.solid,
    "--category-soft": theme.soft,
    "--category-border": theme.border,
    "--category-text": theme.text,
  };
});

const sameRiskDatasets = computed<DatasetSubcategory[]>(() => {
  if (!detail.value) {
    return [];
  }

  const category = enabledCategories.value.find(
    (item) => item.categoryId === detail.value?.category.categoryId,
  );

  return (
    category?.subcategories
      .filter((dataset) => dataset.datasetId !== detail.value?.datasetId)
      .slice(0, 4) ?? []
  );
});

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
  await Promise.all([datasetCatalogStore.fetchCatalog(), loadDetail()]);
});
</script>

<style scoped lang="scss">
.detail-page {
  padding-bottom: 2.5rem;
}

.detail-stack {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  min-width: 0;
}

.detail-summary {
  position: relative;
  overflow: hidden;
  padding: 1.35rem 1.45rem;
  border: 1px solid var(--category-border);
  border-radius: var(--radius-card-md);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(255, 255, 255, 0.82)),
    var(--category-soft);
  box-shadow: var(--shadow-surface-mid);
}

.detail-summary::before {
  content: "";
  position: absolute;
  inset: 0 auto 0 0;
  width: 4px;
  background: var(--category-accent);
}

.detail-summary__copy {
  position: relative;
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 0.75rem;
}

.category-badge {
  display: inline-flex;
  width: fit-content;
  max-width: 100%;
  padding: 0.38rem 0.72rem;
  border: 1px solid var(--category-border);
  border-radius: var(--radius-pill);
  background: rgba(255, 255, 255, 0.74);
  color: var(--category-text);
  font-size: 0.82rem;
  font-weight: 800;
  overflow-wrap: anywhere;
}

.detail-summary__title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  min-width: 0;
}

.detail-summary h1 {
  min-width: 0;
  margin: 0;
  color: var(--color-text-dark);
  font-size: clamp(1.9rem, 3vw, 2.65rem);
  line-height: 1.12;
  letter-spacing: 0;
  overflow-wrap: anywhere;
}

.detail-summary__title-row :deep(.ui-button) {
  flex: 0 1 auto;
  min-width: 0;
}

.detail-summary p {
  margin: 0;
  max-width: 70ch;
  color: var(--color-text-muted);
  font-size: 1rem;
  line-height: 1.72;
  overflow-wrap: anywhere;
}

.detail-summary__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.55rem 1rem;
  color: var(--color-text-subtle);
  font-size: 0.9rem;
  font-weight: 700;
}

.detail-summary__meta strong {
  color: var(--color-text-dark);
  font-variant-numeric: tabular-nums;
}

.detail-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(280px, 0.34fr);
  gap: 1.2rem;
  align-items: start;
}

.detail-main,
.detail-aside {
  min-width: 0;
}

.detail-main {
  display: flex;
  flex-direction: column;
  gap: 1.15rem;
}

.detail-section,
.side-panel {
  min-width: 0;
  border-top: 1px solid var(--color-border-soft);
  padding-top: 1rem;
}

.detail-section h2,
.side-panel h2 {
  margin: 0 0 0.85rem;
  color: var(--color-text-dark);
  font-size: 1.05rem;
  line-height: 1.35;
  overflow-wrap: anywhere;
}

.long-copy {
  max-width: 72ch;
  margin: 0;
  color: var(--color-text-muted);
  font-size: 1rem;
  line-height: 1.9;
  overflow-wrap: anywhere;
}

.numbered-list {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
  margin: 0;
  padding: 0;
  list-style: none;
  counter-reset: detail-list;
}

.numbered-list li {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 0.75rem;
  color: var(--color-text-muted);
  line-height: 1.72;
  counter-increment: detail-list;
}

.numbered-list li::before {
  content: counter(detail-list, decimal-leading-zero);
  color: var(--category-text);
  font-size: 0.82rem;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
}

.numbered-list span {
  min-width: 0;
  overflow-wrap: anywhere;
}

.empty-copy {
  margin: 0;
  color: var(--color-text-subtle);
  line-height: 1.7;
}

.detail-aside {
  position: sticky;
  top: calc(var(--nav-height) + 1rem);
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.side-panel {
  border: 1px solid var(--color-border-soft);
  border-radius: var(--radius-card-sm);
  padding: 1rem;
  background: rgba(255, 255, 255, 0.78);
  box-shadow: var(--shadow-surface-soft);
}

.side-panel h2 {
  margin-bottom: 0.8rem;
  font-size: 0.98rem;
}

.side-facts dl {
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
  margin: 0;
}

.side-facts dl div {
  display: flex;
  flex-direction: column;
  gap: 0.22rem;
}

.side-facts dt {
  color: var(--color-text-subtle);
  font-size: 0.8rem;
  font-weight: 700;
}

.side-facts dd {
  margin: 0;
  color: var(--color-text-dark);
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  overflow-wrap: anywhere;
}

.side-actions {
  display: flex;
  flex-direction: column;
  gap: 0.7rem;
}

.side-actions :deep(.ui-button) {
  min-width: 0;
}

.related-list {
  display: flex;
  align-items: flex-start;
  flex-direction: column;
  gap: 0.35rem;
}

.related-list :deep(a) {
  justify-content: flex-start;
  min-width: 0;
  text-align: left;
}

@media (max-width: 980px) {
  .detail-summary__title-row,
  .detail-layout {
    grid-template-columns: 1fr;
  }

  .detail-summary__title-row {
    flex-direction: column;
  }

  .detail-summary__title-row :deep(button) {
    width: 100%;
  }

  .detail-aside {
    position: static;
    order: -1;
  }

  .side-actions {
    order: -1;
  }
}

@media (max-width: 640px) {
  .detail-summary {
    padding: 1.15rem;
  }

  .detail-summary h1 {
    font-size: 2rem;
  }

  .side-panel {
    padding: 0.95rem;
  }
}
</style>
