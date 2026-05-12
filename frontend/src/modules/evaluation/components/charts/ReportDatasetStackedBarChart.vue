<template>
  <VChart
    class="report-chart"
    :option="option"
    autoresize
    @click="handleChartClick"
    @mouseout="handleChartMouseout"
    @mouseover="handleChartMouseover"
  />
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import VChart from "vue-echarts";
import { ensureEvaluationChartsRegistered } from "@/modules/evaluation/charts/echarts-registry";
import { buildDatasetStackedBarOption } from "@/modules/evaluation/lib/evaluation-report-chart-options";
import type { EvaluationReportPayload } from "@/shared/types/agent-types";

ensureEvaluationChartsRegistered();

const props = defineProps<{
  report: EvaluationReportPayload;
}>();
const { t } = useI18n();

const emit = defineEmits<{
  (event: "preview", datasetId: string | null): void;
  (event: "select", datasetId: string): void;
}>();

const option = computed(() => buildDatasetStackedBarOption(props.report, t));

const getDatasetIdFromEvent = (event: { dataIndex?: number }): string | null => {
  const dataIndex = event.dataIndex;
  if (typeof dataIndex !== "number") {
    return null;
  }

  return props.report.breakdowns.datasetSummaries[dataIndex]?.datasetId ?? null;
};

const handleChartMouseover = (event: { dataIndex?: number }) => {
  emit("preview", getDatasetIdFromEvent(event));
};

const handleChartMouseout = () => {
  emit("preview", null);
};

const handleChartClick = (event: { dataIndex?: number }) => {
  const datasetId = getDatasetIdFromEvent(event);
  if (datasetId) {
    emit("select", datasetId);
  }
};
</script>

<style scoped lang="scss">
.report-chart {
  width: 100%;
  height: 360px;
}
</style>
