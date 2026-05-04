<template>
  <section class="report-section">
    <div class="section-head">
      <div>
        <h2>评分报告</h2>
        <p>{{ stateText }}</p>
      </div>
      <UiButton
        v-if="error"
        variant="secondary"
        size="sm"
        leading-icon="lucide:refresh-cw"
        @click="$emit('retry')"
      >
        重试
      </UiButton>
    </div>

    <div v-if="loading" class="section-state">正在读取报告</div>
    <InlineNotice v-else-if="error" tone="danger" :message="error" />
    <div v-else-if="!report" class="section-state">{{ stateText }}</div>

    <template v-else>
      <div class="report-highlights" aria-label="报告摘要">
        <div
          v-for="item in reportHighlights"
          :key="item.label"
          class="report-highlight"
          :class="`report-highlight--${item.tone}`"
        >
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
          <small>{{ item.caption }}</small>
        </div>
      </div>

      <div class="report-flow">
        <ReportAbilitySection
          :report="report"
          :insight="insightItems[0]"
          :radar-metric-rows="radarMetricRows"
          :confidence-summary="confidenceSummary"
        />
        <ReportOutcomeSection
          :report="report"
          :insight="insightItems[1]"
          :rate-overview-rows="rateOverviewRows"
        />
        <ReportRiskSection
          :report="report"
          :difficulty-insight="difficultyInsight"
          :dataset-insight="datasetInsight"
          @difficulty-preview="handleDifficultyPreview"
          @difficulty-select="handleDifficultySelect"
          @dataset-preview="handleDatasetPreview"
          @dataset-select="handleDatasetSelect"
        />
        <ReportSampleLocationSection
          :report="report"
          :insight="insightItems[4]"
        />
      </div>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import ReportAbilitySection from "@/modules/evaluation/components/ReportAbilitySection.vue";
import ReportOutcomeSection from "@/modules/evaluation/components/ReportOutcomeSection.vue";
import ReportRiskSection from "@/modules/evaluation/components/ReportRiskSection.vue";
import ReportSampleLocationSection from "@/modules/evaluation/components/ReportSampleLocationSection.vue";
import {
  buildReportHighlights,
  buildReportInsights,
  resolveDatasetSummaryInsight,
  resolveDifficultyBucketInsight,
} from "@/modules/evaluation/lib/evaluation-report-insights";
import {
  buildConfidenceSummary,
  buildRadarMetricRows,
  buildRateOverviewRows,
} from "@/modules/evaluation/lib/evaluation-report-metrics";
import type { EvaluationReportPayload } from "@/shared/types/agent-types";
import UiButton from "@/shared/ui/actions/UiButton.vue";
import InlineNotice from "@/shared/ui/feedback/InlineNotice.vue";

const props = defineProps<{
  report: EvaluationReportPayload | null;
  loading: boolean;
  error: string;
  stateText: string;
}>();

defineEmits<{
  (event: "retry"): void;
}>();

const reportHighlights = computed(() =>
  props.report ? buildReportHighlights(props.report) : [],
);
const radarMetricRows = computed(() =>
  props.report ? buildRadarMetricRows(props.report) : [],
);
const rateOverviewRows = computed(() =>
  props.report ? buildRateOverviewRows(props.report) : [],
);
const confidenceSummary = computed(() =>
  props.report ? buildConfidenceSummary(props.report) : null,
);
const insightItems = computed(() =>
  props.report ? buildReportInsights(props.report) : [],
);

const previewDifficultyBucket = ref<string | null>(null);
const lockedDifficultyBucket = ref<string | null>(null);
const previewDatasetId = ref<string | null>(null);
const lockedDatasetId = ref<string | null>(null);

const activeDifficultyBucket = computed(
  () => previewDifficultyBucket.value ?? lockedDifficultyBucket.value,
);
const activeDatasetId = computed(
  () => previewDatasetId.value ?? lockedDatasetId.value,
);

const difficultyInsight = computed(() =>
  props.report
    ? resolveDifficultyBucketInsight(props.report, activeDifficultyBucket.value)
    : null,
);
const datasetInsight = computed(() =>
  props.report
    ? resolveDatasetSummaryInsight(props.report, activeDatasetId.value)
    : null,
);

const handleDifficultyPreview = (bucket: string | null) => {
  previewDifficultyBucket.value = bucket;
};

const handleDifficultySelect = (bucket: string) => {
  lockedDifficultyBucket.value = bucket;
};

const handleDatasetPreview = (datasetId: string | null) => {
  previewDatasetId.value = datasetId;
};

const handleDatasetSelect = (datasetId: string) => {
  lockedDatasetId.value = datasetId;
};

watch(
  () => props.report?.evaluationId,
  () => {
    previewDifficultyBucket.value = null;
    lockedDifficultyBucket.value = null;
    previewDatasetId.value = null;
    lockedDatasetId.value = null;
  },
);
</script>

<style scoped lang="scss">
.report-section,
.report-flow {
  display: flex;
  flex-direction: column;
}

.report-section {
  position: relative;
  gap: 1.45rem;
  padding-top: 1.65rem;
  border-top: 1px solid rgba(148, 163, 184, 0.18);
}

.report-section::before {
  position: absolute;
  top: -1px;
  left: 0;
  width: 8rem;
  height: 1px;
  background: linear-gradient(90deg, #2563eb, rgba(37, 99, 235, 0));
  content: "";
}

.section-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.section-head h2 {
  margin: 0;
  color: var(--color-text-dark);
  font-size: 1.18rem;
}

.section-head p {
  margin: 0.35rem 0 0;
  color: var(--color-text-subtle);
  line-height: 1.68;
}

.section-state {
  display: flex;
  min-height: 180px;
  align-items: center;
  justify-content: center;
  border: 1px dashed rgba(148, 163, 184, 0.28);
  color: var(--color-text-subtle);
}

.report-highlights {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0;
  border-top: 1px solid rgba(148, 163, 184, 0.14);
}

.report-highlight {
  min-width: 0;
  padding: 1rem 1rem 1rem 0.85rem;
  border-left: 3px solid rgba(100, 116, 139, 0.34);
}

.report-highlight span,
.report-highlight small {
  display: block;
  color: var(--color-text-subtle);
  font-size: 0.78rem;
  font-weight: 800;
}

.report-highlight strong {
  display: block;
  margin-top: 0.3rem;
  color: var(--color-text-dark);
  font-size: 1.55rem;
  font-variant-numeric: tabular-nums;
  font-weight: 900;
}

.report-highlight small {
  margin-top: 0.32rem;
  line-height: 1.5;
}

.report-highlight--primary {
  border-color: #2563eb;
}

.report-highlight--success {
  border-color: #16a34a;
}

.report-highlight--warning {
  border-color: #f59e0b;
}

.report-highlight--danger {
  border-color: #dc2626;
}

.report-highlight--neutral {
  border-color: rgba(100, 116, 139, 0.36);
}

.report-flow {
  gap: 1.55rem;
}

@media (max-width: 1080px) {
  .report-highlights {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .section-head {
    flex-direction: column;
  }
}
</style>
