<template>
  <section class="report-unit report-unit--ability">
    <div class="report-unit__copy">
      <span>能力结构</span>
      <h3>{{ insight?.title }}</h3>
      <strong>{{ insight?.value }}</strong>
      <p>{{ insight?.caption }}</p>
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
</template>

<script setup lang="ts">
import { defineAsyncComponent } from "vue";
import type {
  EvaluationConfidenceSummary,
  EvaluationRadarMetricRow,
} from "@/modules/evaluation/lib/evaluation-report-metrics";
import type {
  EvaluationReportInsight,
} from "@/modules/evaluation/lib/evaluation-report-insights";
import type { EvaluationReportPayload } from "@/shared/types/agent-types";

const ReportConfidenceIntervalChart = defineAsyncComponent(
  () =>
    import(
      "@/modules/evaluation/components/charts/ReportConfidenceIntervalChart.vue"
    ),
);
const ReportRadarChart = defineAsyncComponent(
  () => import("@/modules/evaluation/components/charts/ReportRadarChart.vue"),
);

defineProps<{
  report: EvaluationReportPayload;
  insight: EvaluationReportInsight | undefined;
  radarMetricRows: EvaluationRadarMetricRow[];
  confidenceSummary: EvaluationConfidenceSummary | null;
}>();
</script>

<style scoped lang="scss">
.report-unit {
  position: relative;
  min-width: 0;
  overflow: hidden;
  border-top: 1px solid rgba(148, 163, 184, 0.16);
  background:
    radial-gradient(circle at 0% 0%, rgba(37, 99, 235, 0.08), transparent 30%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.62), rgba(248, 250, 252, 0.26));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.78);
}

.report-unit--ability {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1.1rem 1rem 0.7rem;
}

.report-unit__copy {
  min-width: 0;
}

.report-unit__copy span {
  display: block;
  color: var(--color-text-subtle);
  font-size: 0.78rem;
  font-weight: 800;
}

.report-unit__copy h3 {
  margin: 0.28rem 0 0;
  color: var(--color-text-dark);
  font-size: 1rem;
}

.report-unit__copy strong {
  display: block;
  margin-top: 0.3rem;
  color: var(--color-text-dark);
  font-size: 1.55rem;
  font-variant-numeric: tabular-nums;
  font-weight: 900;
}

.report-unit__copy p {
  margin: 0.35rem 0 0;
  color: var(--color-text-subtle);
  line-height: 1.68;
}

.ability-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.06fr) minmax(320px, 0.94fr);
  min-width: 0;
  gap: 1.15rem;
  align-items: stretch;
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

.confidence-strip {
  display: grid;
  grid-template-columns: minmax(220px, 0.32fr) minmax(0, 1fr);
  gap: 1rem;
  align-items: center;
  min-width: 0;
  padding-top: 0.9rem;
  border-top: 1px solid rgba(148, 163, 184, 0.14);
}

.confidence-strip__copy span {
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

.confidence-strip__copy p {
  margin: 0.35rem 0 0;
  color: var(--color-text-subtle);
  line-height: 1.62;
}

.ability-layout :deep(.report-chart) {
  height: 330px;
}

.confidence-strip :deep(.report-chart) {
  height: 150px;
}

@media (max-width: 1080px) {
  .ability-layout,
  .confidence-strip {
    grid-template-columns: 1fr;
  }
}
</style>
