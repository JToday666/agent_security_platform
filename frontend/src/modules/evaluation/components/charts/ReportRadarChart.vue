<template>
  <VChart class="report-chart" :option="option" autoresize />
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import VChart from "vue-echarts";
import { ensureEvaluationChartsRegistered } from "@/modules/evaluation/charts/echarts-registry";
import { buildRadarOption } from "@/modules/evaluation/lib/evaluation-report-chart-options";
import type { EvaluationReportPayload } from "@/shared/types/agent-types";

ensureEvaluationChartsRegistered();

const props = defineProps<{
  report: EvaluationReportPayload;
}>();
const { t } = useI18n();

const option = computed(() => buildRadarOption(props.report, t));
</script>

<style scoped lang="scss">
.report-chart {
  width: 100%;
  height: 340px;
}
</style>
