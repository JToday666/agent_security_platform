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
        <section class="report-unit report-unit--ability">
          <div class="report-unit__copy">
            <span>能力结构</span>
            <h3>{{ insightItems[0]?.title }}</h3>
            <strong>{{ insightItems[0]?.value }}</strong>
            <p>{{ insightItems[0]?.caption }}</p>
          </div>
          <div class="ability-layout">
            <div class="metric-table-wrap">
              <table class="metric-table metric-table--compact">
                <thead>
                  <tr>
                    <th>指标</th>
                    <th>分数</th>
                    <th>解释</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="row in radarMetricRows"
                    :key="row.key"
                    :class="`metric-row--${row.tone}`"
                  >
                    <th scope="row">{{ row.label }}</th>
                    <td class="metric-value">{{ row.value }}</td>
                    <td>{{ row.description }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <ReportRadarChart :report="report" />
          </div>

          <div class="confidence-strip">
            <div class="confidence-strip__copy">
              <span>{{ confidenceSummary?.label }}</span>
              <strong>{{ confidenceSummary?.value }}</strong>
              <p>{{ confidenceSummary?.caption }}</p>
            </div>
            <ReportConfidenceIntervalChart :report="report" />
          </div>
        </section>

        <section class="report-unit report-unit--results">
          <div class="report-unit__copy">
            <span>样本结果</span>
            <h3>{{ insightItems[1]?.title }}</h3>
            <strong>{{ insightItems[1]?.value }}</strong>
            <p>{{ insightItems[1]?.caption }}</p>
          </div>

          <div class="result-layout">
            <div class="chart-pane">
              <ReportOutcomeDonutChart :report="report" />
            </div>
            <div v-if="rateOverviewRows.length" class="chart-pane chart-pane--rates">
              <div class="chart-pane__head">
                <span>结果率概览</span>
                <p>完成率、成功率和条件成功率用于判断样本质量。</p>
              </div>
              <ReportRateOverviewChart :report="report" />
            </div>
          </div>
        </section>

        <div class="chart-grid chart-grid--risk">
          <section class="chart-unit">
            <div class="chart-unit__head">
              <span>难度表现</span>
              <h3>{{ difficultyInsight?.title }}</h3>
              <p>{{ difficultyInsight?.caption }}</p>
            </div>
            <ReportDifficultyBarChart
              :report="report"
              @preview="handleDifficultyPreview"
              @select="handleDifficultySelect"
            />
          </section>

          <section class="chart-unit">
            <div class="chart-unit__head">
              <span>风险类型</span>
              <h3>{{ datasetInsight?.title }}</h3>
              <p>{{ datasetInsight?.caption }}</p>
            </div>
            <ReportDatasetStackedBarChart
              :report="report"
              @preview="handleDatasetPreview"
              @select="handleDatasetSelect"
            />
          </section>
        </div>

        <section class="chart-unit chart-unit--wide">
          <div class="sample-location-layout">
            <div class="report-unit__copy">
              <span>样本定位</span>
              <h3>{{ insightItems[4]?.title }}</h3>
              <strong>{{ insightItems[4]?.value }}</strong>
              <p>{{ insightItems[4]?.caption }}</p>
            </div>
            <ReportSampleScatterChart :report="report" />
          </div>
        </section>
      </div>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import {
  buildConfidenceSummary,
  buildRadarMetricRows,
  buildRateOverviewRows,
  buildReportHighlights,
  buildReportInsights,
  resolveDatasetSummaryInsight,
  resolveDifficultyBucketInsight,
} from "@/modules/evaluation/lib/evaluation-report-view";
import ReportConfidenceIntervalChart from "@/modules/evaluation/components/charts/ReportConfidenceIntervalChart.vue";
import ReportDatasetStackedBarChart from "@/modules/evaluation/components/charts/ReportDatasetStackedBarChart.vue";
import ReportDifficultyBarChart from "@/modules/evaluation/components/charts/ReportDifficultyBarChart.vue";
import ReportOutcomeDonutChart from "@/modules/evaluation/components/charts/ReportOutcomeDonutChart.vue";
import ReportRadarChart from "@/modules/evaluation/components/charts/ReportRadarChart.vue";
import ReportRateOverviewChart from "@/modules/evaluation/components/charts/ReportRateOverviewChart.vue";
import ReportSampleScatterChart from "@/modules/evaluation/components/charts/ReportSampleScatterChart.vue";
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
.report-flow,
.chart-unit {
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

.section-head h2,
.report-unit__copy h3,
.chart-unit__head h3 {
  margin: 0;
  color: var(--color-text-dark);
}

.section-head h2 {
  font-size: 1.18rem;
}

.section-head p,
.report-unit__copy p,
.chart-unit__head p {
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
  transition:
    background var(--duration-base) var(--ease-standard),
    transform var(--duration-base) var(--ease-standard);
}

.report-highlight:hover {
  background: rgba(255, 255, 255, 0.62);
  transform: translateY(-1px);
}

.report-highlight span,
.report-highlight small,
.report-unit__copy span,
.chart-unit__head span {
  display: block;
  color: var(--color-text-subtle);
  font-size: 0.78rem;
  font-weight: 800;
}

.report-highlight strong,
.report-unit__copy strong {
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

.report-unit,
.chart-unit {
  position: relative;
  min-width: 0;
  overflow: hidden;
  border-top: 1px solid rgba(148, 163, 184, 0.16);
  background:
    radial-gradient(circle at 0% 0%, rgba(37, 99, 235, 0.08), transparent 30%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.62), rgba(248, 250, 252, 0.26));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.78);
  animation: report-unit-enter var(--duration-fade-in) var(--ease-emphasized) both;
}

.report-unit--ability,
.report-unit--results {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1.1rem 1rem 0.7rem;
}

.report-unit__copy {
  min-width: 0;
}

.report-unit__copy h3,
.chart-unit__head h3 {
  margin-top: 0.28rem;
  font-size: 1rem;
}

.ability-layout,
.result-layout,
.sample-location-layout {
  display: grid;
  min-width: 0;
  gap: 1.15rem;
  align-items: stretch;
}

.ability-layout {
  grid-template-columns: minmax(0, 1.06fr) minmax(320px, 0.94fr);
}

.result-layout {
  grid-template-columns: minmax(280px, 0.85fr) minmax(0, 1fr);
}

.sample-location-layout {
  grid-template-columns: minmax(220px, 0.28fr) minmax(0, 1fr);
  align-items: center;
}

.confidence-strip {
  display: grid;
  grid-template-columns: minmax(220px, 0.32fr) minmax(0, 1fr);
  gap: 1rem;
  align-items: center;
  min-width: 0;
  padding-top: 0.9rem;
  border-top: 1px solid rgba(148, 163, 184, 0.14);
}

.confidence-strip__copy span,
.chart-pane__head span {
  display: block;
  color: var(--color-text-subtle);
  font-size: 0.78rem;
  font-weight: 800;
}

.confidence-strip__copy strong {
  display: block;
  margin-top: 0.28rem;
  color: var(--color-text-dark);
  font-size: 1.35rem;
  font-variant-numeric: tabular-nums;
  font-weight: 900;
}

.confidence-strip__copy p,
.chart-pane__head p {
  margin: 0.35rem 0 0;
  color: var(--color-text-subtle);
  line-height: 1.62;
}

.chart-pane {
  min-width: 0;
  border-top: 1px solid rgba(148, 163, 184, 0.12);
}

.chart-pane--rates {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.metric-table-wrap {
  min-width: 0;
  overflow-x: auto;
}

.metric-table {
  width: 100%;
  min-width: 640px;
  border-collapse: collapse;
}

.metric-table--compact {
  min-width: 560px;
}

.metric-table th,
.metric-table td {
  padding: 0.8rem 0.75rem;
  border-bottom: 1px solid rgba(148, 163, 184, 0.16);
  color: var(--color-text-muted);
  line-height: 1.62;
  text-align: left;
  vertical-align: top;
}

.metric-table thead th {
  color: var(--color-text-subtle);
  font-size: 0.82rem;
  font-weight: 800;
}

.metric-table tbody th,
.metric-value {
  color: var(--color-text-dark);
  font-weight: 850;
}

.metric-table tbody tr {
  transition:
    background var(--duration-base) var(--ease-standard),
    transform var(--duration-base) var(--ease-standard);
}

.metric-table tbody tr:hover {
  background: rgba(255, 255, 255, 0.68);
}

.metric-value {
  border-left: 3px solid rgba(100, 116, 139, 0.3);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.metric-row--primary .metric-value {
  border-left-color: #2563eb;
}

.metric-row--success .metric-value {
  border-left-color: #16a34a;
}

.metric-row--warning .metric-value {
  border-left-color: #f59e0b;
}

.metric-row--danger .metric-value {
  border-left-color: #dc2626;
}

.chart-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1.5rem;
}

.chart-unit {
  gap: 0.85rem;
  padding: 1.1rem 1rem 0.45rem;
}

.chart-unit--wide {
  grid-column: 1 / -1;
}

.ability-layout :deep(.report-chart),
.chart-unit :deep(.report-chart) {
  height: 330px;
}

.result-layout .chart-pane :deep(.report-chart) {
  height: 320px;
}

.chart-pane--rates :deep(.report-chart) {
  height: 260px;
}

.confidence-strip :deep(.report-chart) {
  height: 150px;
}

.chart-unit--wide :deep(.report-chart) {
  height: 360px;
}

@keyframes report-unit-enter {
  from {
    opacity: 0;
    transform: translateY(10px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 1080px) {
  .report-highlights,
  .ability-layout,
  .result-layout,
  .sample-location-layout,
  .confidence-strip,
  .chart-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .section-head {
    flex-direction: column;
  }

  .report-unit,
  .chart-unit {
    margin-inline: -0.15rem;
  }

  .chart-unit :deep(.report-chart),
  .ability-layout :deep(.report-chart),
  .result-layout .chart-pane :deep(.report-chart),
  .chart-unit--wide :deep(.report-chart) {
    height: 300px;
  }

  .confidence-strip :deep(.report-chart),
  .chart-pane--rates :deep(.report-chart) {
    height: 230px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .report-unit,
  .chart-unit,
  .report-highlight,
  .metric-table tbody tr {
    animation: none;
    transition: none;
  }

  .report-highlight:hover {
    transform: none;
  }
}
</style>
