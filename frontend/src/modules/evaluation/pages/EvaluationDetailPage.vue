<template>
  <div class="content detail-page layout-page-shell">
    <PageHeroCard
      :title="detail?.agentName || '评测详情'"
      :description="detail?.description || '查看任务状态、报告摘要和详细指标。'"
      density="compact"
      title-tone="brand"
    >
      <template #actions>
        <UiButton variant="secondary" @click="goBack">返回记录</UiButton>
      </template>
    </PageHeroCard>

    <div v-if="loading && !detail" class="state-card layout-state-card ui-surface-white">
      <h2>正在读取评测详情</h2>
      <p>请稍候。</p>
    </div>

    <div v-else-if="error && !detail" class="state-card layout-state-card ui-surface-white">
      <h2>详情加载失败</h2>
      <p>{{ error }}</p>
      <UiButton variant="primary" @click="loadDetail()">重试</UiButton>
    </div>

    <template v-else-if="detail">
      <section class="status-grid">
        <article class="status-card ui-surface-white">
          <div class="status-head">
            <span class="status-label">任务状态</span>
            <StatusTag kind="evaluation" :value="detail.status" size="sm" />
          </div>
        </article>

        <article class="status-card ui-surface-white">
          <div class="status-head">
            <span class="status-label">提交方式</span>
            <StatusTag kind="method" :value="detail.submitMethod" size="sm" />
          </div>
        </article>

        <article class="status-card ui-surface-white">
          <div class="status-head">
            <span class="status-label">数据集数量</span>
            <strong class="status-count">{{ detail.datasetNames.length }}</strong>
          </div>
        </article>

        <article class="status-card ui-surface-white">
          <div class="status-head">
            <span class="status-label">报告状态</span>
            <StatusTag kind="report" :value="reportTagValue" size="sm" />
          </div>
        </article>
      </section>

      <InlineNotice v-if="error" tone="danger" title="操作未完成" :message="error" />

      <section v-if="hasAvailableActions(detail.controls)" class="actions-panel ui-surface-white">
        <div class="panel-head panel-head--compact">
          <div>
            <h2>任务操作</h2>
            <p>仅显示当前状态下可执行的操作。</p>
          </div>
        </div>

        <div class="action-buttons">
          <UiButton
            v-if="detail.controls.canPause"
            variant="secondary"
            :disabled="actionLoading"
            @click="openActionDialog('pause')"
          >
            暂停
          </UiButton>
          <UiButton
            v-if="detail.controls.canResume"
            variant="primary"
            :disabled="actionLoading"
            @click="runAction('resume')"
          >
            继续
          </UiButton>
          <UiButton
            v-if="detail.controls.canTerminate"
            variant="secondary"
            :disabled="actionLoading"
            @click="openActionDialog('terminate')"
          >
            终止
          </UiButton>
          <UiButton
            v-if="detail.controls.canCancel"
            variant="danger"
            :disabled="actionLoading"
            @click="openActionDialog('cancel')"
          >
            取消
          </UiButton>
        </div>
      </section>

      <section class="report-panel ui-surface-white">
        <div class="panel-head">
          <div>
            <h2>报告摘要</h2>
            <p>{{ reportStateText }}</p>
          </div>
          <UiButton
            v-if="detail.report?.reportUri"
            :href="detail.report.reportUri"
            target="_blank"
            variant="secondary"
          >
            打开报告
          </UiButton>
        </div>

        <div v-if="detail.report" class="report-meta">
          <span>生成时间：{{ formatDateTimeLabel(detail.report.generatedAt) }}</span>
          <span v-if="hasVisibleScore(detail.score, detail.finalReportAvailable)">
            综合得分：{{ formatEvaluationScore(detail.score, detail.finalReportAvailable) }}
          </span>
        </div>

        <InlineNotice v-if="!detail.report" tone="info" :message="reportStateText" />

        <template v-else>
          <div class="summary-metrics">
            <MetricCard
              v-for="item in summaryMetrics"
              :key="item.label"
              :label="item.label"
              :value="item.value"
              :description="item.description"
            />
          </div>

          <div class="summary-groups">
            <article class="summary-group ui-surface-panel">
              <h3>风险分类</h3>
              <p v-if="detail.report.summary.byRiskCategory.length === 0" class="empty-copy">
                暂无风险分类汇总。
              </p>
              <ul v-else class="summary-list">
                <li v-for="item in detail.report.summary.byRiskCategory" :key="`${item.categoryId}-${item.name}`">
                  {{ item.name || item.categoryId }}：样本 {{ item.totalSamples }}，风险 {{ item.harmDetectedCount }}
                </li>
              </ul>
            </article>

            <article class="summary-group ui-surface-panel">
              <h3>风险等级</h3>
              <p v-if="detail.report.summary.byRiskLevel.length === 0" class="empty-copy">
                暂无风险等级汇总。
              </p>
              <ul v-else class="summary-list">
                <li v-for="item in detail.report.summary.byRiskLevel" :key="`risk-${item.level}`">
                  等级 {{ item.level }}：样本 {{ item.totalSamples }}，风险 {{ item.harmDetectedCount }}
                </li>
              </ul>
            </article>

            <article class="summary-group ui-surface-panel">
              <h3>攻击等级</h3>
              <p v-if="detail.report.summary.byAttackLevel.length === 0" class="empty-copy">
                暂无攻击等级汇总。
              </p>
              <ul v-else class="summary-list">
                <li v-for="item in detail.report.summary.byAttackLevel" :key="`attack-${item.level}`">
                  等级 {{ item.level }}：样本 {{ item.totalSamples }}，风险 {{ item.harmDetectedCount }}
                </li>
              </ul>
            </article>
          </div>

          <InlineNotice
            v-for="warning in detail.report.warnings"
            :key="warning"
            tone="warning"
            :message="warning"
          />

          <div v-if="detail.report.metrics.length" class="detail-metrics">
            <article
              v-for="metric in detail.report.metrics"
              :key="metric.name"
              class="metric-detail ui-surface-panel"
            >
              <div class="metric-head">
                <strong>{{ metric.name }}</strong>
                <span>{{ metric.value }}</span>
              </div>
              <div class="progress-bar progress-bar--secondary">
                <div class="progress-fill" :style="{ width: `${metric.percentage}%` }"></div>
              </div>
              <p>{{ metric.description }}</p>
            </article>
          </div>
          <InlineNotice v-else tone="info" message="当前结果未返回详细指标。" />
        </template>
      </section>
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
import { computed } from "vue";
import PageHeroCard from "@/shared/ui/page/PageHeroCard.vue";
import ConfirmDialog from "@/shared/ui/feedback/ConfirmDialog.vue";
import InlineNotice from "@/shared/ui/feedback/InlineNotice.vue";
import MetricCard from "@/shared/ui/display/MetricCard.vue";
import StatusTag from "@/shared/ui/display/StatusTag.vue";
import UiButton from "@/shared/ui/actions/UiButton.vue";
import { formatDateTimeLabel } from "@/modules/dataset/lib/dataset-utils";
import { useEvaluationDetailPage } from "@/modules/evaluation/composables/useEvaluationDetailPage";
import {
  formatEvaluationScore,
  hasAvailableActions,
  hasVisibleScore,
} from "@/modules/evaluation/lib/evaluation-status";

const {
  detail,
  loading,
  error,
  reportStateText,
  actionLoading,
  actionDialogVisible,
  actionDialogTitle,
  actionDialogMessage,
  actionDialogConfirmText,
  actionDialogDanger,
  loadDetail,
  goBack,
  openActionDialog,
  runAction,
  confirmAction,
} = useEvaluationDetailPage();

const reportTagValue = computed(() => {
  if (!detail.value) {
    return "pending";
  }

  if (detail.value.report) {
    return "available";
  }

  if (
    detail.value.status === "completed" ||
    detail.value.status === "terminated" ||
    detail.value.status === "failed" ||
    detail.value.status === "canceled"
  ) {
    return "missing";
  }

  return "pending";
});

const summaryMetrics = computed(() => {
  if (!detail.value?.report) {
    return [];
  }

  const items = [
    {
      label: "总样本数",
      value: String(detail.value.report.summary.totalSamples),
      description: "报告统计的样本总量",
    },
    {
      label: "已完成样本",
      value: String(detail.value.report.summary.completedSamples),
      description: "已完成执行的样本数量",
    },
    {
      label: "完成任务数",
      value: String(detail.value.report.summary.taskCompletedCount),
      description: "完成评测的数据集数量",
    },
    {
      label: "检测到风险",
      value: String(detail.value.report.summary.harmDetectedCount),
      description: "命中风险的样本数量",
    },
    {
      label: "失败数量",
      value: String(detail.value.report.summary.failedCount),
      description: "执行失败的样本数量",
    },
  ];

  if (hasVisibleScore(detail.value.score, detail.value.finalReportAvailable)) {
    items.unshift({
      label: "综合得分",
      value: formatEvaluationScore(detail.value.score, detail.value.finalReportAvailable),
      description: "仅在后端返回最终报告后显示",
    });
  }

  return items;
});
</script>

<style scoped lang="scss">
.detail-page {
  padding-bottom: 2.5rem;
}

.status-grid,
.summary-metrics,
.summary-groups,
.detail-metrics {
  display: grid;
  gap: 0.9rem;
}

.status-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.status-card,
.actions-panel,
.report-panel {
  border-radius: 1.25rem;
  padding: 1.15rem;
}

.status-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.9rem;
}

.status-label {
  color: var(--color-text-subtle);
  font-size: 0.82rem;
}

.status-count {
  color: var(--color-text-dark);
  font-size: 1.15rem;
  line-height: 1;
}

.panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.panel-head h2 {
  margin: 0;
  color: var(--color-text-dark);
}

.panel-head p {
  margin: 0.42rem 0 0;
  color: var(--color-text-subtle);
  line-height: 1.68;
}

.actions-panel,
.report-panel {
  margin-top: 1rem;
}

.progress-bar {
  width: 100%;
  height: 10px;
  margin-top: 0.9rem;
  border-radius: 999px;
  overflow: hidden;
  background: rgba(226, 232, 240, 0.92);
}

.progress-bar--secondary {
  height: 8px;
  margin-top: 0.65rem;
}

.progress-fill {
  height: 100%;
  background: var(--grad-progress);
}

.progress-meta,
.report-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-top: 0.9rem;
  color: var(--color-text-subtle);
}

.action-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-top: 0.9rem;
}

.summary-metrics {
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
  margin-top: 1rem;
}

.summary-groups {
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin-top: 1rem;
}

.summary-group {
  border-radius: 1rem;
  padding: 1rem;
}

.summary-group h3 {
  margin: 0;
  color: var(--color-text-dark);
}

.summary-list,
.empty-copy {
  margin: 0.75rem 0 0;
  color: var(--color-text-subtle);
  line-height: 1.7;
}

.summary-list {
  padding-left: 1rem;
}

.detail-metrics {
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  margin-top: 1rem;
}

.metric-detail {
  border-radius: 1rem;
  padding: 1rem;
}

.metric-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.8rem;
}

.metric-head strong {
  color: var(--color-text-dark);
}

.metric-head span,
.metric-detail p {
  color: var(--color-text-subtle);
}

.metric-detail p {
  margin: 0.75rem 0 0;
  line-height: 1.65;
}

@media (max-width: 1080px) {
  .status-grid,
  .summary-groups {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .status-grid,
  .summary-groups,
  .detail-metrics {
    grid-template-columns: 1fr;
  }

  .panel-head,
  .action-buttons,
  .status-head {
    flex-direction: column;
    align-items: stretch;
  }

  .progress-meta,
  .report-meta {
    flex-direction: column;
    gap: 0.45rem;
  }
}
</style>
