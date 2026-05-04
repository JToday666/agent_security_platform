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
import VChart from "vue-echarts";
import { ensureEvaluationChartsRegistered } from "@/modules/evaluation/charts/echarts-registry";
import { buildDifficultyBarOption } from "@/modules/evaluation/lib/evaluation-report-chart-options";
import type { EvaluationReportPayload } from "@/shared/types/agent-types";

ensureEvaluationChartsRegistered();

const props = defineProps<{
  report: EvaluationReportPayload;
}>();

const emit = defineEmits<{
  (event: "preview", bucket: string | null): void;
  (event: "select", bucket: string): void;
}>();

const option = computed(() => buildDifficultyBarOption(props.report));

const getBucketFromEvent = (event: { dataIndex?: number }): string | null => {
  const dataIndex = event.dataIndex;
  if (typeof dataIndex !== "number") {
    return null;
  }

  return props.report.breakdowns.difficultyBuckets[dataIndex]?.bucket ?? null;
};

const handleChartMouseover = (event: { dataIndex?: number }) => {
  emit("preview", getBucketFromEvent(event));
};

const handleChartMouseout = () => {
  emit("preview", null);
};

const handleChartClick = (event: { dataIndex?: number }) => {
  const bucket = getBucketFromEvent(event);
  if (bucket) {
    emit("select", bucket);
  }
};
</script>

<style scoped lang="scss">
.report-chart {
  width: 100%;
  height: 340px;
}
</style>
