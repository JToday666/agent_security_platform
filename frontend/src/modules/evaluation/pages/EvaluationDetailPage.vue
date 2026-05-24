<template>
  <div class="content detail-page layout-page-shell layout-page-shell--wide">
    <PageHero
      :title="detail?.agentName || t('evaluation.detail.titleFallback')"
      :description="t('evaluation.detail.description')"
    >
      <template #actions>
        <UiButton
          variant="secondary"
          leading-icon="app:action.back"
          @click="goBack"
        >
          {{ t("evaluation.actions.backToRecords") }}
        </UiButton>
      </template>
    </PageHero>

    <PageStatePanel
      v-if="loading && !detail"
      :title="t('evaluation.detail.loadingTitle')"
      :message="t('common.feedback.pleaseWait')"
      :loading="true"
    />

    <PageStatePanel
      v-else-if="error && !detail"
      :title="t('evaluation.detail.errorTitle')"
      :message="error"
      :action-text="t('evaluation.actions.retry')"
      @action="loadDetail()"
    />

    <template v-else-if="detail">
      <EvaluationSummaryBand
        :detail="detail"
        :score-tone="scoreTone"
        :primary-score="primaryScore"
        :score-caption="scoreCaption"
        :report-tag-value="reportTagValue"
        :summary-items="summaryItems"
        :action-loading="actionLoading"
        @open-action="openActionDialog"
        @run-action="runAction"
      />

      <InlineNotice
        v-if="error"
        tone="danger"
        :title="t('evaluation.detail.operationFailedTitle')"
        :message="error"
      />

      <EvaluationSampleOutcomePanel
        :completion-rate="completionRate"
        :segments="sampleSegments"
        :stats="sampleStats"
      />

      <EvaluationDetailGroupsPanel :groups="detailGroups" />

      <EvaluationReportSection
        :report="report"
        :loading="reportLoading"
        :error="reportError"
        :state-text="reportStateText"
        @retry="loadReport"
      />

      <EvaluationEvidenceSection
        :detail="detail"
        :download-loading="downloadLoading"
        :download-error="downloadError"
        @download="downloadSampleDetails"
      />
    </template>

    <ConfirmDialog
      v-model="actionDialogVisible"
      :title="actionDialogTitle"
      :message="actionDialogMessage"
      :confirm-text="actionDialogConfirmText"
      :cancel-text="t('evaluation.actions.back')"
      :danger="actionDialogDanger"
      :loading="actionLoading"
      @confirm="confirmAction"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import EvaluationDetailGroupsPanel from "@/modules/evaluation/components/EvaluationDetailGroupsPanel.vue";
import EvaluationEvidenceSection from "@/modules/evaluation/components/EvaluationEvidenceSection.vue";
import EvaluationReportSection from "@/modules/evaluation/components/EvaluationReportSection.vue";
import EvaluationSampleOutcomePanel from "@/modules/evaluation/components/EvaluationSampleOutcomePanel.vue";
import EvaluationSummaryBand from "@/modules/evaluation/components/EvaluationSummaryBand.vue";
import { useEvaluationDetailPage } from "@/modules/evaluation/composables/useEvaluationDetailPage";
import {
  buildEvaluationDetailGroups,
  buildEvaluationSampleBase,
  buildEvaluationSampleSegments,
  buildEvaluationSampleStats,
  buildEvaluationSummaryItems,
  formatEvaluationPrimaryScore,
  getEvaluationCompletionRate,
  getEvaluationReportTagValue,
  getEvaluationScoreCaption,
  resolveEvaluationPrimaryScoreValue,
  resolveEvaluationScoreTone,
} from "@/modules/evaluation/lib/evaluation-detail-view";
import UiButton from "@/shared/ui/actions/UiButton.vue";
import ConfirmDialog from "@/shared/ui/feedback/ConfirmDialog.vue";
import InlineNotice from "@/shared/ui/feedback/InlineNotice.vue";
import PageStatePanel from "@/shared/ui/feedback/PageStatePanel.vue";
import PageHero from "@/shared/ui/page/PageHero.vue";

const { t } = useI18n();

const {
  detail,
  loading,
  error,
  report,
  reportLoading,
  reportError,
  reportStateText,
  downloadLoading,
  downloadError,
  actionLoading,
  actionDialogVisible,
  actionDialogTitle,
  actionDialogMessage,
  actionDialogConfirmText,
  actionDialogDanger,
  loadDetail,
  loadReport,
  goBack,
  downloadSampleDetails,
  openActionDialog,
  runAction,
  confirmAction,
} = useEvaluationDetailPage();

const scoreTone = computed(() =>
  detail.value
    ? resolveEvaluationScoreTone(
        resolveEvaluationPrimaryScoreValue(detail.value, report.value),
      )
    : "neutral",
);

const primaryScore = computed(() =>
  detail.value ? formatEvaluationPrimaryScore(detail.value, report.value) : "--",
);

const scoreCaption = computed(() =>
  detail.value ? getEvaluationScoreCaption(detail.value, t, report.value) : "",
);

const reportTagValue = computed(() =>
  detail.value ? getEvaluationReportTagValue(detail.value, report.value) : "pending",
);

const summaryItems = computed(() =>
  detail.value ? buildEvaluationSummaryItems(detail.value, t) : [],
);

const sampleBase = computed(() =>
  detail.value
    ? buildEvaluationSampleBase(detail.value, report.value)
    : { total: 0, success: 0, failed: 0, error: 0, completed: 0 },
);

const completionRate = computed(() => getEvaluationCompletionRate(sampleBase.value));

const sampleSegments = computed(() =>
  buildEvaluationSampleSegments(sampleBase.value, t),
);

const sampleStats = computed(() =>
  buildEvaluationSampleStats(sampleBase.value, completionRate.value, t),
);

const detailGroups = computed(() =>
  detail.value ? buildEvaluationDetailGroups(detail.value, report.value, t) : [],
);
</script>

<style scoped lang="scss">
.detail-page {
  display: flex;
  flex-direction: column;
  gap: 1.6rem;
  padding-bottom: 2.5rem;
}
</style>
