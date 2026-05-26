<template>
  <VChart class="report-chart" :option="option" autoresize />
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import VChart from "vue-echarts";
import { ensureEvaluationChartsRegistered } from "@/modules/evaluation/charts/echarts-registry";
import { buildSampleScatterOption } from "@/modules/evaluation/lib/evaluation-report-chart-options";
import type {
  EvaluationChartAxisMode,
  EvaluationReportPayload,
} from "@/shared/types/agent-types";

ensureEvaluationChartsRegistered();

const props = defineProps<{
  report: EvaluationReportPayload;
  axisMode: EvaluationChartAxisMode;
}>();
const { t } = useI18n();

const option = computed(() =>
  buildSampleScatterOption(props.report, t, props.axisMode),
);
</script>

<style scoped lang="scss">
.report-chart {
  width: 100%;
  height: 360px;
}
</style>
