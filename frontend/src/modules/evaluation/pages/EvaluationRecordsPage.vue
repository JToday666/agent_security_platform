<template>
  <div class="content records-page layout-page-shell layout-page-shell--wide">
    <PageHero
      :title="t('evaluation.records.title')"
      :description="t('evaluation.records.description')"
    >
      <template #actions>
        <UiButton
          :to="RouteLocation.agentSubmit"
          variant="secondary"
          leading-icon="app:action.submitEvaluation"
        >
          {{ t("common.actions.submitEvaluation") }}
        </UiButton>
      </template>
    </PageHero>

    <PageStatePanel
      v-if="loading"
      :title="t('evaluation.records.loadingTitle')"
      :message="t('common.feedback.pleaseWait')"
      :loading="true"
    />

    <PageStatePanel
      v-else-if="error"
      :title="t('evaluation.records.errorTitle')"
      :message="error"
      :action-text="t('evaluation.actions.retry')"
      @action="loadRecords"
    />

    <div v-else-if="records.length" class="records-shell">
      <EvaluationTrendPanel @select="openEvaluationDetail" />

      <EvaluationFilterBar
        :search="search"
        :status="status"
        :visibility="visibility"
        :submit-method="submitMethod"
        @update:search="search = $event"
        @update:status="status = $event"
        @update:visibility="visibility = $event"
        @update:submitMethod="submitMethod = $event"
      />

      <div class="result-bar">
        <span>
          {{
            t("evaluation.records.resultSummary", {
              visible: filteredRecords.length,
              total: records.length,
            })
          }}
        </span>
      </div>

      <div v-if="filteredRecords.length" class="records-list">
        <EvaluationRecordItem
          v-for="record in filteredRecords"
          :key="record.evaluationId"
          :record="record"
        />
      </div>

      <PageStatePanel
        v-else
        :title="t('evaluation.records.noMatchTitle')"
        :message="t('evaluation.records.noMatchMessage')"
        tone="default"
      />
    </div>

    <PageStatePanel
      v-else
      :title="t('evaluation.records.emptyTitle')"
      :message="t('evaluation.records.emptyMessage')"
      :action-text="t('evaluation.actions.submitNow')"
      @action="$router.push(RouteLocation.agentSubmit)"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import { useRouter } from "vue-router";
import { RouteLocation } from "@/app/router/route-names";
import { getEvaluationRecords } from "@/modules/evaluation/api/evaluation-api";
import EvaluationFilterBar from "@/modules/evaluation/components/EvaluationFilterBar.vue";
import EvaluationRecordItem from "@/modules/evaluation/components/EvaluationRecordItem.vue";
import EvaluationTrendPanel from "@/modules/evaluation/components/EvaluationTrendPanel.vue";
import {
  filterEvaluationRecords,
  type EvaluationRecordFilterVisibility,
} from "@/modules/evaluation/lib/evaluation-record-filters";
import type {
  EvaluationRecord,
  EvaluationStatus,
  SubmitMethod,
} from "@/shared/types/agent-types";
import { getErrorMessage } from "@/shared/composables/useAsyncState";
import UiButton from "@/shared/ui/actions/UiButton.vue";
import PageStatePanel from "@/shared/ui/feedback/PageStatePanel.vue";
import PageHero from "@/shared/ui/page/PageHero.vue";

const $router = useRouter();
const { t } = useI18n();
const records = ref<EvaluationRecord[]>([]);
const loading = ref(true);
const error = ref("");

const search = ref("");
const status = ref<"all" | EvaluationStatus>("all");
const visibility = ref<EvaluationRecordFilterVisibility>("all");
const submitMethod = ref<"all" | SubmitMethod>("all");

const filteredRecords = computed(() =>
  filterEvaluationRecords(records.value, {
    status: status.value,
    visibility: visibility.value,
    submitMethod: submitMethod.value,
    search: search.value,
  }),
);

const loadRecords = async () => {
  loading.value = true;
  error.value = "";

  try {
    records.value = await getEvaluationRecords();
  } catch (loadError) {
    error.value =
      getErrorMessage(loadError, t("evaluation.api.recordsLoadFailed"));
  } finally {
    loading.value = false;
  }
};

const openEvaluationDetail = (evaluationId: string) => {
  void $router.push(RouteLocation.evaluationDetail(evaluationId));
};

onMounted(async () => {
  await loadRecords();
});
</script>

<style scoped lang="scss">
.records-page {
  padding-bottom: 2.5rem;
}

.records-shell {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.result-bar {
  padding: 0.15rem 0 0;
  color: var(--color-text-muted);
  font-size: 0.92rem;
}

.records-list {
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
}
</style>
