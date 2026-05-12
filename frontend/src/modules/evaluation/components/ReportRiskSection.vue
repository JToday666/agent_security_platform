<template>
  <div class="chart-grid chart-grid--risk">
    <section class="chart-unit">
      <div class="chart-unit__head">
        <span>{{ t("evaluation.report.difficultySection") }}</span>
        <h3>{{ difficultyInsight?.title }}</h3>
        <p>{{ difficultyInsight?.caption }}</p>
      </div>
      <ReportDifficultyBarChart
        :report="report"
        @preview="$emit('difficulty-preview', $event)"
        @select="$emit('difficulty-select', $event)"
      />
    </section>

    <section class="chart-unit">
      <div class="chart-unit__head">
        <span>{{ t("evaluation.report.difficultyRisk") }}</span>
        <h3>{{ datasetInsight?.title }}</h3>
        <p>{{ datasetInsight?.caption }}</p>
      </div>
      <ReportDatasetStackedBarChart
        :report="report"
        @preview="$emit('dataset-preview', $event)"
        @select="$emit('dataset-select', $event)"
      />
    </section>
  </div>
</template>

<script setup lang="ts">
import { defineAsyncComponent } from "vue";
import { useI18n } from "vue-i18n";
import type {
  EvaluationSelectableInsight,
} from "@/modules/evaluation/lib/evaluation-report-insights";
import type { EvaluationReportPayload } from "@/shared/types/agent-types";

const ReportDatasetStackedBarChart = defineAsyncComponent(
  () =>
    import(
      "@/modules/evaluation/components/charts/ReportDatasetStackedBarChart.vue"
    ),
);
const ReportDifficultyBarChart = defineAsyncComponent(
  () =>
    import("@/modules/evaluation/components/charts/ReportDifficultyBarChart.vue"),
);

defineProps<{
  report: EvaluationReportPayload;
  difficultyInsight: EvaluationSelectableInsight | null;
  datasetInsight: EvaluationSelectableInsight | null;
}>();

defineEmits<{
  (event: "difficulty-preview", bucket: string | null): void;
  (event: "difficulty-select", bucket: string): void;
  (event: "dataset-preview", datasetId: string | null): void;
  (event: "dataset-select", datasetId: string): void;
}>();

const { t } = useI18n();
</script>

<style scoped lang="scss">
.chart-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1.5rem;
}

.chart-unit {
  position: relative;
  display: flex;
  min-width: 0;
  overflow: hidden;
  flex-direction: column;
  gap: 0.85rem;
  padding: 1.1rem 1rem 0.45rem;
  border-top: 1px solid rgba(148, 163, 184, 0.16);
  background:
    radial-gradient(circle at 0% 0%, rgba(37, 99, 235, 0.08), transparent 30%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.62), rgba(248, 250, 252, 0.26));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.78);
}

.chart-unit__head span {
  display: block;
  color: var(--color-text-subtle);
  font-size: 0.78rem;
  font-weight: 800;
}

.chart-unit__head h3 {
  margin: 0.28rem 0 0;
  color: var(--color-text-dark);
  font-size: 1rem;
}

.chart-unit__head p {
  margin: 0.35rem 0 0;
  color: var(--color-text-subtle);
  line-height: 1.68;
}

.chart-unit :deep(.report-chart) {
  height: 330px;
}

@media (max-width: 1080px) {
  .chart-grid {
    grid-template-columns: 1fr;
  }
}
</style>
