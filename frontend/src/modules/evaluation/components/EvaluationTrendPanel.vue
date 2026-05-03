<template>
  <section class="trend-panel">
    <div class="trend-panel__head">
      <div>
        <h2>分数趋势</h2>
        <p>查看近期或全部已生成报告的评测变化。</p>
      </div>

      <div class="trend-panel__controls" aria-label="趋势图筛选">
        <div class="segmented" aria-label="趋势范围">
          <button
            v-for="item in scopeOptions"
            :key="item.value"
            type="button"
            :class="{ active: scope === item.value }"
            @click="scope = item.value"
          >
            {{ item.label }}
          </button>
        </div>
        <div class="segmented" aria-label="趋势视图">
          <button
            v-for="item in viewOptions"
            :key="item.value"
            type="button"
            :class="{ active: view === item.value }"
            @click="view = item.value"
          >
            {{ item.label }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="loading" class="trend-panel__state">正在读取趋势</div>
    <div v-else-if="error" class="trend-panel__state trend-panel__state--error">
      <span>{{ error }}</span>
      <UiButton variant="text" size="sm" @click="loadTrend">重试</UiButton>
    </div>
    <div v-else-if="!trend?.items.length" class="trend-panel__state">
      暂无可展示趋势。
    </div>
    <div v-else class="trend-canvas">
      <div class="trend-canvas__summary" aria-label="趋势摘要">
        <div class="trend-summary trend-summary--primary">
          <span>{{ trendSummary.latestLabel }}</span>
          <strong>{{ trendSummary.latestValue }}</strong>
        </div>
        <div class="trend-summary" :class="`trend-summary--${trendSummary.deltaTone}`">
          <span>{{ trendSummary.deltaLabel }}</span>
          <strong>{{ trendSummary.deltaValue }}</strong>
        </div>
        <div class="trend-summary trend-summary--neutral">
          <span>{{ trendSummary.sampleLabel }}</span>
          <strong>{{ trendSummary.sampleValue }}</strong>
        </div>
      </div>

      <EvaluationTrendChart
        :trend="trend"
        :view="view"
        @select="$emit('select', $event)"
      />
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { getEvaluationScoreTrend } from "@/modules/evaluation/api/evaluation-api";
import EvaluationTrendChart from "@/modules/evaluation/components/charts/EvaluationTrendChart.vue";
import { buildTrendSummary } from "@/modules/evaluation/lib/evaluation-report-view";
import type {
  EvaluationScoreTrend,
  EvaluationScoreTrendScope,
  EvaluationScoreTrendView,
} from "@/shared/types/agent-types";
import UiButton from "@/shared/ui/actions/UiButton.vue";

defineEmits<{
  (event: "select", evaluationId: string): void;
}>();

const scopeOptions: Array<{ label: string; value: EvaluationScoreTrendScope }> = [
  { label: "最近 10 次", value: "recent10" },
  { label: "全部评测", value: "all" },
];

const viewOptions: Array<{ label: string; value: EvaluationScoreTrendView }> = [
  { label: "能力视图", value: "capability" },
  { label: "风险视图", value: "risk" },
];

const scope = ref<EvaluationScoreTrendScope>("recent10");
const view = ref<EvaluationScoreTrendView>("capability");
const trend = ref<EvaluationScoreTrend | null>(null);
const loading = ref(false);
const error = ref("");
const trendSummary = computed(() => buildTrendSummary(trend.value, view.value));

const loadTrend = async () => {
  loading.value = true;
  error.value = "";

  try {
    trend.value = await getEvaluationScoreTrend(scope.value);
    view.value = trend.value.defaultView;
  } catch (loadError) {
    trend.value = null;
    error.value =
      loadError instanceof Error ? loadError.message : "评测趋势加载失败。";
  } finally {
    loading.value = false;
  }
};

watch(scope, () => {
  void loadTrend();
});

onMounted(() => {
  void loadTrend();
});
</script>

<style scoped lang="scss">
.trend-panel {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 1.15rem;
  padding-top: 1.35rem;
  border-top: 1px solid rgba(148, 163, 184, 0.18);
}

.trend-panel::before {
  position: absolute;
  top: -1px;
  left: 0;
  width: 8rem;
  height: 1px;
  background: linear-gradient(90deg, #2563eb, rgba(37, 99, 235, 0));
  content: "";
}

.trend-panel__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.trend-panel__head h2 {
  margin: 0;
  color: var(--color-text-dark);
  font-size: 1.22rem;
}

.trend-panel__head p {
  margin: 0.35rem 0 0;
  color: var(--color-text-subtle);
  line-height: 1.68;
}

.trend-panel__controls,
.segmented {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.segmented {
  padding: 0.2rem;
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: var(--radius-pill);
  background: rgba(255, 255, 255, 0.68);
  box-shadow: 0 14px 28px -26px rgba(15, 23, 42, 0.26);
  backdrop-filter: blur(var(--blur-8));
}

.segmented button {
  min-height: 2.25rem;
  padding: 0 0.8rem;
  border: 0;
  border-radius: var(--radius-pill);
  background: transparent;
  color: var(--color-text-muted);
  cursor: pointer;
  font-weight: 700;
  transition:
    background var(--duration-base) var(--ease-standard),
    color var(--duration-base) var(--ease-standard),
    transform var(--duration-fast) var(--ease-standard),
    box-shadow var(--duration-base) var(--ease-standard);
}

.segmented button:hover {
  color: var(--color-primary);
  transform: translateY(-1px);
}

.segmented button.active {
  background: var(--color-white);
  color: var(--color-primary);
  box-shadow: var(--shadow-control);
}

.trend-canvas {
  position: relative;
  overflow: hidden;
  padding: 1rem 1rem 0.45rem;
  border: 1px solid rgba(148, 163, 184, 0.16);
  background:
    radial-gradient(circle at 8% 0%, rgba(37, 99, 235, 0.1), transparent 32%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.72), rgba(248, 250, 252, 0.42));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.86);
  animation: trend-panel-enter var(--duration-fade-in) var(--ease-emphasized) both;
}

.trend-canvas__summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.75rem;
}

.trend-summary {
  min-width: 0;
  padding: 0.8rem 0.9rem;
  border-left: 3px solid rgba(100, 116, 139, 0.32);
  background: rgba(255, 255, 255, 0.58);
  transition:
    background var(--duration-base) var(--ease-standard),
    transform var(--duration-base) var(--ease-standard);
}

.trend-summary:hover {
  background: rgba(255, 255, 255, 0.84);
  transform: translateY(-1px);
}

.trend-summary span {
  display: block;
  color: var(--color-text-subtle);
  font-size: 0.78rem;
  font-weight: 800;
}

.trend-summary strong {
  display: block;
  margin-top: 0.28rem;
  color: var(--color-text-dark);
  font-size: 1.22rem;
  font-variant-numeric: tabular-nums;
}

.trend-summary--primary {
  border-color: #2563eb;
}

.trend-summary--success {
  border-color: #16a34a;
}

.trend-summary--danger {
  border-color: #dc2626;
}

.trend-summary--warning {
  border-color: #f59e0b;
}

.trend-summary--neutral {
  border-color: rgba(100, 116, 139, 0.38);
}

:global(.evaluation-chart-tooltip) {
  border: 1px solid rgba(148, 163, 184, 0.18) !important;
  border-radius: 10px !important;
  box-shadow: 0 20px 42px -24px rgba(15, 23, 42, 0.28) !important;
  color: var(--color-text-dark) !important;
  line-height: 1.65 !important;
}

.trend-panel__state {
  display: flex;
  min-height: 220px;
  align-items: center;
  justify-content: center;
  gap: 0.8rem;
  border: 1px dashed rgba(148, 163, 184, 0.28);
  border-radius: 0;
  color: var(--color-text-subtle);
}

.trend-panel__state--error {
  color: #b91c1c;
}

@media (max-width: 900px) {
  .trend-panel__head,
  .trend-panel__controls {
    flex-direction: column;
    align-items: stretch;
  }
}

@media (max-width: 640px) {
  .trend-canvas {
    padding-inline: 0.75rem;
  }

  .trend-canvas__summary {
    grid-template-columns: 1fr;
  }

  .segmented {
    width: 100%;
    overflow-x: auto;
  }

  .segmented button {
    flex: 1;
  }
}

@keyframes trend-panel-enter {
  from {
    opacity: 0;
    transform: translateY(10px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (prefers-reduced-motion: reduce) {
  .trend-canvas,
  .segmented button,
  .trend-summary {
    animation: none;
    transition: none;
  }

  .segmented button:hover,
  .trend-summary:hover {
    transform: none;
  }
}
</style>
