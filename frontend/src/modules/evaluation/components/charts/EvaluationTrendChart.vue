<template>
  <VChart
    class="evaluation-chart"
    :option="option"
    autoresize
    @click="handleChartClick"
  />
</template>

<script setup lang="ts">
import { computed } from "vue";
import VChart from "vue-echarts";
import { ensureEvaluationChartsRegistered } from "@/modules/evaluation/charts/echarts-registry";
import { buildTrendLineOption } from "@/modules/evaluation/lib/evaluation-report-view";
import type {
  EvaluationScoreTrend,
  EvaluationScoreTrendView,
} from "@/shared/types/agent-types";

ensureEvaluationChartsRegistered();

const props = defineProps<{
  trend: EvaluationScoreTrend | null;
  view: EvaluationScoreTrendView;
}>();

const emit = defineEmits<{
  (event: "select", evaluationId: string): void;
}>();

const option = computed(() => buildTrendLineOption(props.trend, props.view));

const handleChartClick = (event: { dataIndex?: number }) => {
  const dataIndex = event.dataIndex;
  if (typeof dataIndex !== "number") {
    return;
  }

  const evaluationId = props.trend?.items[dataIndex]?.evaluationId;
  if (evaluationId) {
    emit("select", evaluationId);
  }
};
</script>

<style scoped lang="scss">
.evaluation-chart {
  width: 100%;
  height: 380px;
  cursor: pointer;
}

@media (max-width: 768px) {
  .evaluation-chart {
    height: 300px;
  }
}
</style>
