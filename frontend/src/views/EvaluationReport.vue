<template>
  <div class="content report-card layout-page-panel layout-page-panel--md ui-surface-glass">
    <h1 class="page-title layout-page-title">评测详情</h1>
    <p class="report-id">任务 ID：{{ evaluationId }}</p>

    <div v-if="loading" class="state-card layout-state-card ui-surface-white">
      <h2>正在读取评测详情</h2>
      <p>系统正在同步该任务的执行状态和最新指标。</p>
    </div>

    <div v-else-if="error" class="state-card layout-state-card ui-surface-white">
      <h2>详情加载失败</h2>
      <p>{{ error }}</p>
      <button class="retry-btn layout-retry-btn ui-btn ui-btn-pill ui-btn-gradient" @click="loadDetail">
        重试
      </button>
    </div>

    <template v-else-if="report">
      <div class="summary-section ui-surface-white">
        <div class="summary-item">
          <span class="label">智能体名称</span>
          <span class="value">{{ report.agentName }}</span>
        </div>
        <div class="summary-item">
          <span class="label">评测状态</span>
          <span class="value" :class="report.status">{{ statusLabels[report.status] }}</span>
        </div>
        <div class="summary-item">
          <span class="label">提交方式</span>
          <span class="value">{{ report.submitMethod.toUpperCase() }}</span>
        </div>
        <div class="summary-item">
          <span class="label">综合得分</span>
          <span class="value score">{{ report.score ? `${report.score} 分` : "待生成" }}</span>
        </div>
      </div>

      <div class="summary-panel ui-surface-white">
        <p class="summary-text">{{ report.summary }}</p>
        <p class="summary-meta">
          数据集：{{ report.datasetNames.join("、") }} · 创建时间：{{ formatDateTimeLabel(report.createdAt) }}
        </p>
      </div>

      <div v-if="report.warnings.length" class="warnings ui-surface-white">
        <h2>提示</h2>
        <p v-for="warning in report.warnings" :key="warning">{{ warning }}</p>
      </div>

      <h2 class="section-title">详细指标</h2>
      <div class="metrics-grid">
        <div
          v-for="metric in report.metrics"
          :key="metric.name"
          class="metric-item ui-surface-white"
        >
          <div class="metric-header">
            <span class="metric-name">{{ metric.name }}</span>
            <span class="metric-value">{{ metric.value }}</span>
          </div>
          <div class="progress-bar">
            <div
              class="progress-fill"
              :style="{ width: metric.percentage + '%' }"
            ></div>
          </div>
          <p class="metric-desc">{{ metric.description }}</p>
        </div>
      </div>

      <div class="actions">
        <button class="back-btn ui-btn ui-btn-pill" @click="goBack">
          返回评测记录
        </button>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { getEvaluationDetail } from "@/api/AgentService";
import { RouteLocation } from "@/router/RouteNames";
import type { EvaluationDetail } from "@/types/AgentTypes";
import { formatDateTimeLabel } from "@/utils/DatasetUtils";

const route = useRoute();
const router = useRouter();
// 旧 report/:id 已在路由层被重定向，这里只读取规范参数。
const evaluationId = String(route.params.evaluationId ?? "");

const report = ref<EvaluationDetail | null>(null);
const loading = ref(true);
const error = ref("");

const statusLabels = {
  pending: "排队中",
  running: "执行中",
  completed: "已完成",
};

const loadDetail = async () => {
  loading.value = true;
  error.value = "";

  try {
    report.value = await getEvaluationDetail(evaluationId);
  } catch (loadError) {
    error.value =
      loadError instanceof Error ? loadError.message : "评测详情加载失败。";
  } finally {
    loading.value = false;
  }
};

const goBack = () => {
  router.push(RouteLocation.userCenter);
};

onMounted(async () => {
  await loadDetail();
});
</script>

<style scoped>
.report-id {
  font-size: 1rem;
  color: #64748b;
  margin-bottom: 1.6rem;
}

.summary-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 1rem;
  border-radius: 1.2rem;
  padding: 1.3rem;
}

.summary-item {
  display: flex;
  flex-direction: column;
}

.label {
  color: #64748b;
  font-size: 0.84rem;
  margin-bottom: 0.35rem;
}

.value {
  color: #0f172a;
  font-size: 1.15rem;
  font-weight: 700;
}

.value.pending {
  color: #c2410c;
}

.value.running {
  color: #2563eb;
}

.value.completed {
  color: #15803d;
}

.score {
  color: #7c3aed;
}

.summary-panel,
.warnings {
  margin-top: 1rem;
  border-radius: 1.2rem;
  padding: 1.2rem;
}

.summary-text {
  margin: 0;
  color: #334155;
  line-height: 1.8;
}

.summary-meta {
  margin: 0.8rem 0 0;
  color: #64748b;
}

.warnings h2 {
  margin: 0;
  color: #0f172a;
  font-size: 1.1rem;
}

.warnings p {
  margin: 0.7rem 0 0;
  color: #c2410c;
  line-height: 1.7;
}

.section-title {
  margin: 1.8rem 0 1rem;
  color: #0f172a;
}

.metrics-grid {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.metric-item {
  padding: 1.15rem;
  border-radius: 1.1rem;
}

.metric-header {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
}

.metric-name {
  color: #0f172a;
  font-weight: 700;
}

.metric-value {
  color: #2563eb;
  font-weight: 700;
}

.progress-bar {
  width: 100%;
  height: 8px;
  border-radius: 999px;
  overflow: hidden;
  background: #e2e8f0;
  margin-top: 0.7rem;
}

.progress-fill {
  height: 100%;
  background: var(--grad-progress);
}

.metric-desc {
  margin: 0.7rem 0 0;
  color: #64748b;
  line-height: 1.6;
}

.actions {
  margin-top: 1.5rem;
  text-align: right;
}

.back-btn {
  padding: 0.82rem 1.2rem;
}

@media (max-width: 768px) {
  .actions {
    text-align: initial;
  }

  .back-btn {
    width: 100%;
  }
}
</style>
