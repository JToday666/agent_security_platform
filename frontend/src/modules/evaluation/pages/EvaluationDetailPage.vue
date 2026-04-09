<template>
  <div class="content report-card layout-page-panel layout-page-panel--md ui-surface-glass">
    <h1 class="page-title layout-page-title">评测详情</h1>
    <p class="report-id">任务 ID：{{ evaluationId }}</p>

    <div v-if="loading && !detail" class="state-card layout-state-card ui-surface-white">
      <h2>正在读取评测详情</h2>
      <p>系统正在同步该任务的执行状态和最新指标。</p>
    </div>

    <div v-else-if="error && !detail" class="state-card layout-state-card ui-surface-white">
      <h2>详情加载失败</h2>
      <p>{{ error }}</p>
      <button class="retry-btn layout-retry-btn ui-btn ui-btn-pill ui-btn-gradient" @click="loadDetail()">
        重试
      </button>
    </div>

    <template v-else-if="detail">
      <div class="summary-section ui-surface-white">
        <div class="summary-item">
          <span class="label">智能体名称</span>
          <span class="value">{{ detail.agentName }}</span>
        </div>
        <div class="summary-item">
          <span class="label">评测状态</span>
          <span class="value" :class="getEvaluationStatusTone(detail.status)">
            {{ getEvaluationStatusLabel(detail.status) }}
          </span>
        </div>
        <div class="summary-item">
          <span class="label">提交方式</span>
          <span class="value">{{ detail.submitMethod.toUpperCase() }}</span>
        </div>
        <div class="summary-item">
          <span class="label">综合得分</span>
          <span class="value score">{{ formatEvaluationScore(detail.score, detail.finalReportAvailable) }}</span>
        </div>
      </div>

      <div v-if="error" class="inline-error ui-surface-white">
        {{ error }}
      </div>

      <div class="progress-panel ui-surface-white">
        <div class="progress-head">
          <div>
            <h2>任务进度</h2>
            <p>{{ detail.progress.statusText }}</p>
          </div>
          <strong>{{ detail.progress.percent }}%</strong>
        </div>

        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: `${detail.progress.percent}%` }"></div>
        </div>

        <div class="progress-meta">
          <span>已完成 {{ detail.progress.completedDatasetCount }} / {{ detail.progress.totalDatasetCount }}</span>
          <span v-if="detail.progress.runningDatasetName">当前数据集：{{ detail.progress.runningDatasetName }}</span>
          <span v-if="detail.progress.pauseDeadlineAt">最晚恢复时间：{{ formatDateTimeLabel(detail.progress.pauseDeadlineAt) }}</span>
          <span v-if="getFinalizationReasonLabel(detail.finalizationReason)">
            {{ getFinalizationReasonLabel(detail.finalizationReason) }}
          </span>
        </div>
      </div>

      <div v-if="hasAvailableActions(detail.controls)" class="actions-panel ui-surface-white">
        <div class="action-buttons">
          <button
            v-if="detail.controls.canPause"
            class="ui-btn ui-btn-pill"
            type="button"
            :disabled="actionLoading"
            @click="openActionDialog('pause')"
          >
            暂停
          </button>
          <button
            v-if="detail.controls.canResume"
            class="ui-btn ui-btn-pill ui-btn-gradient"
            type="button"
            :disabled="actionLoading"
            @click="runAction('resume')"
          >
            继续
          </button>
          <button
            v-if="detail.controls.canTerminate"
            class="ui-btn ui-btn-pill"
            type="button"
            :disabled="actionLoading"
            @click="openActionDialog('terminate')"
          >
            终止
          </button>
          <button
            v-if="detail.controls.canCancel"
            class="ui-btn ui-btn-pill ui-btn-danger"
            type="button"
            :disabled="actionLoading"
            @click="openActionDialog('cancel')"
          >
            取消
          </button>
        </div>
      </div>

      <div v-if="detail.report" class="summary-panel ui-surface-white">
        <p class="summary-text">{{ reportStateText }}</p>
        <p class="summary-meta">
          评测项：{{ detail.datasetNames.join("、") }}
          · 报告生成时间：{{ formatDateTimeLabel(detail.report.generatedAt) }}
        </p>
      </div>

      <div v-else-if="detail.status === 'canceled' || detail.status === 'failed'" class="summary-panel ui-surface-white">
        <p class="summary-text">{{ detail.progress.statusText }}</p>
        <p class="summary-meta">当前任务未生成最终报告。</p>
      </div>

      <template v-if="detail.report">
        <h2 class="section-title">报告摘要</h2>
        <div class="summary-cards">
          <div class="metric-item ui-surface-white">
            <div class="metric-header">
              <span class="metric-name">总样本数</span>
              <span class="metric-value">{{ detail.report.summary.totalSamples }}</span>
            </div>
          </div>
          <div class="metric-item ui-surface-white">
            <div class="metric-header">
              <span class="metric-name">已完成样本</span>
              <span class="metric-value">{{ detail.report.summary.completedSamples }}</span>
            </div>
          </div>
          <div class="metric-item ui-surface-white">
            <div class="metric-header">
              <span class="metric-name">完成任务数</span>
              <span class="metric-value">{{ detail.report.summary.taskCompletedCount }}</span>
            </div>
          </div>
          <div class="metric-item ui-surface-white">
            <div class="metric-header">
              <span class="metric-name">检测到风险</span>
              <span class="metric-value">{{ detail.report.summary.harmDetectedCount }}</span>
            </div>
          </div>
          <div class="metric-item ui-surface-white">
            <div class="metric-header">
              <span class="metric-name">失败数量</span>
              <span class="metric-value">{{ detail.report.summary.failedCount }}</span>
            </div>
          </div>
        </div>

        <div class="metrics-grid report-group-grid">
          <div class="metric-item ui-surface-white">
            <div class="metric-header">
              <span class="metric-name">风险分类</span>
              <span class="metric-value">{{ detail.report.summary.byRiskCategory.length }}</span>
            </div>
            <p
              v-for="item in detail.report.summary.byRiskCategory"
              :key="`${item.categoryId}-${item.name}`"
              class="metric-desc"
            >
              {{ item.name || item.categoryId }}：样本 {{ item.totalSamples }}，完成 {{ item.taskCompletedCount }}，风险 {{ item.harmDetectedCount }}
            </p>
            <p v-if="!detail.report.summary.byRiskCategory.length" class="metric-desc">暂无风险分类汇总。</p>
          </div>

          <div class="metric-item ui-surface-white">
            <div class="metric-header">
              <span class="metric-name">风险等级</span>
              <span class="metric-value">{{ detail.report.summary.byRiskLevel.length }}</span>
            </div>
            <p
              v-for="item in detail.report.summary.byRiskLevel"
              :key="`risk-${item.level}`"
              class="metric-desc"
            >
              等级 {{ item.level }}：样本 {{ item.totalSamples }}，风险 {{ item.harmDetectedCount }}
            </p>
            <p v-if="!detail.report.summary.byRiskLevel.length" class="metric-desc">暂无风险等级汇总。</p>
          </div>

          <div class="metric-item ui-surface-white">
            <div class="metric-header">
              <span class="metric-name">攻击等级</span>
              <span class="metric-value">{{ detail.report.summary.byAttackLevel.length }}</span>
            </div>
            <p
              v-for="item in detail.report.summary.byAttackLevel"
              :key="`attack-${item.level}`"
              class="metric-desc"
            >
              等级 {{ item.level }}：样本 {{ item.totalSamples }}，风险 {{ item.harmDetectedCount }}
            </p>
            <p v-if="!detail.report.summary.byAttackLevel.length" class="metric-desc">暂无攻击等级汇总。</p>
          </div>
        </div>
      </template>

      <div v-if="detail.report?.warnings.length" class="warnings ui-surface-white">
        <h2>提示</h2>
        <p v-for="warning in detail.report.warnings" :key="warning">{{ warning }}</p>
      </div>

      <template v-if="detail.report">
        <h2 class="section-title">详细指标</h2>
        <div class="metrics-grid">
          <div
            v-for="metric in detail.report.metrics"
            :key="metric.name"
            class="metric-item ui-surface-white"
          >
            <div class="metric-header">
              <span class="metric-name">{{ metric.name }}</span>
              <span class="metric-value">{{ metric.value }}</span>
            </div>
            <div class="progress-bar secondary">
              <div
                class="progress-fill"
                :style="{ width: `${metric.percentage}%` }"
              ></div>
            </div>
            <p class="metric-desc">{{ metric.description }}</p>
          </div>
        </div>
      </template>

      <div class="actions footer-actions">
        <button class="back-btn ui-btn ui-btn-pill" @click="goBack">
          返回评测记录
        </button>
      </div>
    </template>

    <ConfirmDialog
      v-model="actionDialogVisible"
      :title="actionDialogTitle"
      :message="actionDialogMessage"
      :confirm-text="actionDialogConfirmText"
      cancel-text="返回"
      :danger="actionDialogDanger"
      :loading="actionLoading"
      @confirm="confirmAction"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  getEvaluationDetail,
  postEvaluationAction,
} from "@/modules/evaluation/api";
import ConfirmDialog from "@/shared/ui/ConfirmDialog.vue";
import { RouteLocation } from "@/app/router/RouteNames";
import type {
  EvaluationAction,
  EvaluationDetail,
} from "@/shared/types/AgentTypes";
import { formatDateTimeLabel } from "@/modules/dataset/lib";
import {
  formatEvaluationScore,
  getEvaluationStatusLabel,
  getEvaluationStatusTone,
  getFinalizationReasonLabel,
  hasAvailableActions,
  shouldPollEvaluation,
} from "@/modules/evaluation/lib";

const route = useRoute();
const router = useRouter();
const evaluationId = computed(() => String(route.params.evaluationId ?? ""));

const detail = ref<EvaluationDetail | null>(null);
const loading = ref(true);
const error = ref("");
const actionLoading = ref(false);
const pendingAction = ref<EvaluationAction | null>(null);
const actionDialogVisible = ref(false);
const actionDialogTitle = ref("");
const actionDialogMessage = ref("");
const actionDialogConfirmText = ref("确认");
const actionDialogDanger = ref(false);

let pollTimer: number | null = null;

const reportStateText = computed(() => {
  if (detail.value?.report) {
    return "报告已生成，可查看摘要统计与报告链接。";
  }

  if (!detail.value) {
    return "正在同步报告状态。";
  }

  if (detail.value.status === "canceled" || detail.value.status === "failed") {
    return "当前任务未生成最终报告。";
  }

  if (detail.value.status === "completed" || detail.value.status === "terminated") {
    return "任务已结束，但当前未返回报告内容。";
  }

  return "报告尚未生成，请等待任务继续执行。";
});

const getErrorCode = (value: unknown): number | null => {
  if (!value || typeof value !== "object" || !("code" in value)) {
    return null;
  }

  const code = Number((value as { code?: unknown }).code);
  return Number.isFinite(code) ? code : null;
};

const clearPolling = () => {
  if (pollTimer !== null) {
    window.clearInterval(pollTimer);
    pollTimer = null;
  }
};

const syncPolling = () => {
  clearPolling();

  if (!detail.value || !shouldPollEvaluation(detail.value.status)) {
    return;
  }

  pollTimer = window.setInterval(() => {
    void loadDetail(true);
  }, 600000);
};

const loadDetail = async (silent = false) => {
  if (!silent || !detail.value) {
    loading.value = true;
  }

  if (!silent) {
    error.value = "";
  }

  try {
    detail.value = await getEvaluationDetail(evaluationId.value);
    error.value = "";
    syncPolling();
  } catch (loadError) {
    error.value =
      loadError instanceof Error ? loadError.message : "评测详情加载失败。";
    clearPolling();
  } finally {
    loading.value = false;
  }
};

const applyDetail = (nextDetail: EvaluationDetail) => {
  detail.value = nextDetail;
  error.value = "";
  syncPolling();
};

const goBack = () => {
  router.push(RouteLocation.userCenter);
};

const openActionDialog = (action: EvaluationAction) => {
  pendingAction.value = action;
  actionDialogDanger.value = action === "cancel";
  actionDialogConfirmText.value =
    action === "pause"
      ? "确认暂停"
      : action === "terminate"
        ? "确认终止"
        : "确认取消";

  if (action === "pause") {
    actionDialogTitle.value = "暂停任务";
    actionDialogMessage.value =
      "暂停会在当前数据集跑完后生效，任务最多只能暂停一次。";
  } else if (action === "terminate") {
    actionDialogTitle.value = "终止任务";
    actionDialogMessage.value =
      "终止会在当前数据集跑完后结束剩余队列，并生成最终报告。";
  } else {
    actionDialogTitle.value = "取消任务";
    actionDialogMessage.value =
      "取消会直接中断当前任务，并且不会生成最终报告。";
  }

  actionDialogVisible.value = true;
};

const runAction = async (action: EvaluationAction) => {
  actionLoading.value = true;
  error.value = "";

  try {
    const nextDetail = await postEvaluationAction(evaluationId.value, action);
    applyDetail(nextDetail);
  } catch (actionError) {
    const code = getErrorCode(actionError);
    const message =
      actionError instanceof Error ? actionError.message : "任务操作失败。";
    error.value = message;

    if (code === 40901 || code === 40902) {
      await loadDetail(true);
      error.value = message;
    }
  } finally {
    actionLoading.value = false;
  }
};

const confirmAction = async () => {
  if (!pendingAction.value) {
    return;
  }

  const action = pendingAction.value;
  await runAction(action);
  pendingAction.value = null;
  actionDialogVisible.value = false;
};

watch(
  evaluationId,
  async () => {
    clearPolling();
    detail.value = null;
    await loadDetail();
  },
);

onMounted(async () => {
  await loadDetail();
});

onBeforeUnmount(() => {
  clearPolling();
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

.value.pending,
.value.running {
  color: #2563eb;
}

.value.paused,
.value.terminated {
  color: #b45309;
}

.value.completed {
  color: #15803d;
}

.value.canceled,
.value.failed {
  color: #b91c1c;
}

.score {
  color: #7c3aed;
}

.inline-error,
.progress-panel,
.summary-panel,
.warnings,
.actions-panel {
  margin-top: 1rem;
  border-radius: 1.2rem;
  padding: 1.2rem;
}

.inline-error {
  color: #b91c1c;
}

.progress-head {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: flex-start;
}

.progress-head h2,
.warnings h2 {
  margin: 0;
  color: #0f172a;
  font-size: 1.1rem;
}

.progress-head p,
.summary-text,
.metric-desc,
.warnings p {
  line-height: 1.7;
}

.progress-head p,
.summary-text {
  margin: 0.45rem 0 0;
  color: #334155;
}

.progress-head strong {
  color: #2563eb;
  font-size: 1.4rem;
}

.progress-bar {
  width: 100%;
  height: 10px;
  border-radius: 999px;
  overflow: hidden;
  background: #e2e8f0;
  margin-top: 0.9rem;
}

.progress-bar.secondary {
  height: 8px;
  margin-top: 0.7rem;
}

.progress-fill {
  height: 100%;
  background: var(--grad-progress);
  transition: width 0.3s ease;
}

.progress-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-top: 0.9rem;
  color: #64748b;
}

.action-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.summary-meta {
  margin: 0.8rem 0 0;
  color: #64748b;
}

.section-title {
  margin: 1.8rem 0 1rem;
  color: #0f172a;
}

.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
  margin-bottom: 1rem;
}

.metrics-grid {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.report-group-grid {
  margin-bottom: 1rem;
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

.metric-desc {
  margin: 0.7rem 0 0;
  color: #64748b;
}

.footer-actions {
  margin-top: 1.5rem;
  text-align: right;
}

.back-btn {
  padding: 0.82rem 1.2rem;
}

@media (max-width: 768px) {
  .progress-head,
  .footer-actions {
    text-align: initial;
  }

  .progress-head {
    flex-direction: column;
  }

  .progress-meta {
    flex-direction: column;
    gap: 0.5rem;
  }

  .action-buttons > * {
    flex: 1 1 100%;
  }

  .metric-header {
    flex-direction: column;
    gap: 0.35rem;
  }

  .summary-section {
    grid-template-columns: 1fr;
  }

  .back-btn {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .summary-section,
  .inline-error,
  .progress-panel,
  .summary-panel,
  .warnings,
  .actions-panel,
  .metric-item {
    padding: 1rem;
  }

  .progress-head strong {
    font-size: 1.2rem;
  }
}
</style>
