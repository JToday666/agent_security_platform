<template>
  <VChart class="report-chart" :option="option" autoresize />
</template>

<script setup lang="ts">
import { computed } from "vue";
import VChart from "vue-echarts";
import { ensureEvaluationChartsRegistered } from "@/modules/evaluation/charts/echarts-registry";
import { buildOutcomeDonutOption } from "@/modules/evaluation/lib/evaluation-report-view";
import type { EvaluationReportPayload } from "@/shared/types/agent-types";

ensureEvaluationChartsRegistered();

const props = defineProps<{
  report: EvaluationReportPayload;
}>();

const option = computed(() => buildOutcomeDonutOption(props.report));
</script>

<style scoped lang="scss">
.report-chart {
  width: 100%;
  height: 340px;
}
</style>
