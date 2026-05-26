<template>
  <section class="chart-unit chart-unit--wide">
    <div class="sample-location-layout">
      <div class="report-unit__copy">
        <span>{{ t("evaluation.report.sampleLocationTitle") }}</span>
        <h3>{{ insight?.title }}</h3>
        <strong>{{ insight?.value }}</strong>
        <p>{{ insight?.caption }}</p>
        <div
          class="sample-location-axis"
          :aria-label="t('evaluation.report.sampleLocationAxisAria')"
        >
          <button
            v-for="item in axisModeOptions"
            :key="item.value"
            type="button"
            :class="{ active: axisMode === item.value }"
            @click="axisMode = item.value"
          >
            {{ item.label }}
          </button>
        </div>
      </div>
      <ReportSampleScatterChart :report="report" :axis-mode="axisMode" />
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, defineAsyncComponent, ref } from "vue";
import { useI18n } from "vue-i18n";
import type { EvaluationReportInsight } from "@/modules/evaluation/lib/evaluation-report-insights";
import type {
  EvaluationChartAxisMode,
  EvaluationReportPayload,
} from "@/shared/types/agent-types";

const ReportSampleScatterChart = defineAsyncComponent(
  () =>
    import("@/modules/evaluation/components/charts/ReportSampleScatterChart.vue"),
);

defineProps<{
  report: EvaluationReportPayload;
  insight: EvaluationReportInsight | undefined;
}>();

const { t } = useI18n();
const axisMode = ref<EvaluationChartAxisMode>("full");
const axisModeOptions = computed<Array<{
  label: string;
  value: EvaluationChartAxisMode;
}>>(() => [
  { label: t("evaluation.report.sampleLocationAxisFull"), value: "full" },
  { label: t("evaluation.report.sampleLocationAxisFocus"), value: "focus" },
]);
</script>

<style scoped lang="scss">
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

.chart-unit--wide {
  grid-column: 1 / -1;
}

.sample-location-layout {
  display: grid;
  grid-template-columns: minmax(220px, 0.28fr) minmax(0, 1fr);
  min-width: 0;
  gap: 1.15rem;
  align-items: center;
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

.sample-location-axis {
  display: inline-flex;
  max-width: 100%;
  gap: 0.25rem;
  margin-top: 0.75rem;
  padding: 0.2rem;
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: var(--radius-pill);
  background: rgba(255, 255, 255, 0.68);
}

.sample-location-axis button {
  min-height: 2rem;
  min-width: 0;
  padding: 0 0.68rem;
  border: 0;
  border-radius: var(--radius-pill);
  background: transparent;
  color: var(--color-text-muted);
  cursor: pointer;
  font-weight: 750;
}

.sample-location-axis button.active {
  background: var(--color-white);
  color: var(--color-primary);
  box-shadow: var(--shadow-control);
}

.chart-unit--wide :deep(.report-chart) {
  height: 360px;
}

@media (max-width: 1080px) {
  .sample-location-layout {
    grid-template-columns: 1fr;
  }
}
</style>
