<template>
  <section class="report-unit report-unit--results">
    <div class="report-unit__copy">
      <span>{{ t("evaluation.report.outcomeSection") }}</span>
      <h3>{{ insight?.title }}</h3>
      <strong>{{ insight?.value }}</strong>
      <p>{{ insight?.caption }}</p>
    </div>

    <div class="result-layout">
      <div class="chart-pane">
        <ReportOutcomeDonutChart :report="report" />
      </div>
      <div v-if="rateOverviewRows.length" class="chart-pane chart-pane--rates">
        <div class="chart-pane__head">
          <span>{{ t("evaluation.report.rateOverviewTitle") }}</span>
          <p>{{ t("evaluation.report.rateOverviewDescription") }}</p>
        </div>
        <ReportRateOverviewChart :report="report" />
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { defineAsyncComponent } from "vue";
import { useI18n } from "vue-i18n";
import type {
  EvaluationReportInsight,
} from "@/modules/evaluation/lib/evaluation-report-insights";
import type {
  EvaluationRateOverviewRow,
} from "@/modules/evaluation/lib/evaluation-report-metrics";
import type { EvaluationReportPayload } from "@/shared/types/agent-types";

const ReportOutcomeDonutChart = defineAsyncComponent(
  () =>
    import("@/modules/evaluation/components/charts/ReportOutcomeDonutChart.vue"),
);
const ReportRateOverviewChart = defineAsyncComponent(
  () =>
    import("@/modules/evaluation/components/charts/ReportRateOverviewChart.vue"),
);

defineProps<{
  report: EvaluationReportPayload;
  insight: EvaluationReportInsight | undefined;
  rateOverviewRows: EvaluationRateOverviewRow[];
}>();

const { t } = useI18n();
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

.report-unit--results {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1.1rem 1rem 0.7rem;
}

.report-unit__copy span,
.chart-pane__head span {
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

.report-unit__copy p,
.chart-pane__head p {
  margin: 0.35rem 0 0;
  color: var(--color-text-subtle);
  line-height: 1.68;
}

.result-layout {
  display: grid;
  grid-template-columns: minmax(280px, 0.85fr) minmax(0, 1fr);
  min-width: 0;
  gap: 1.15rem;
  align-items: stretch;
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

.result-layout .chart-pane :deep(.report-chart) {
  height: 320px;
}

.chart-pane--rates :deep(.report-chart) {
  height: 260px;
}

@media (max-width: 1080px) {
  .result-layout {
    grid-template-columns: 1fr;
  }
}
</style>
