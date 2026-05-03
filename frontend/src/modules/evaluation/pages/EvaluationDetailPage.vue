<template>
  <div class="content detail-page layout-page-shell layout-page-shell--wide">
    <PageHero
      :title="detail?.agentName || '评测详情'"
      description="查看任务状态、评分报告和样本证据。"
    >
      <template #actions>
        <UiButton
          variant="secondary"
          leading-icon="lucide:arrow-left"
          @click="goBack"
        >
          返回记录
        </UiButton>
      </template>
    </PageHero>

    <PageStatePanel
      v-if="loading && !detail"
      title="正在读取评测详情"
      message="请稍候。"
      :loading="true"
    />

    <PageStatePanel
      v-else-if="error && !detail"
      title="详情加载失败"
      :message="error"
      action-text="重试"
      @action="loadDetail()"
    />

    <template v-else-if="detail">
      <section class="summary-band" :class="`summary-band--${scoreTone}`">
        <div class="score-display">
          <span>综合分</span>
          <strong>{{ primaryScore }}</strong>
          <small>{{ scoreCaption }}</small>
        </div>

        <div class="summary-band__main">
          <div class="identity-line">
            <code :title="detail.evaluationId">{{ detail.evaluationId }}</code>
            <StatusTag kind="evaluation" :value="detail.status" size="sm" />
            <StatusTag kind="report" :value="reportTagValue" size="sm" />
          </div>

          <p class="status-copy">{{ detail.progress.statusText }}</p>

          <div class="progress-line" aria-label="完成进度">
            <span :style="{ width: `${detail.progress.percent}%` }"></span>
          </div>

          <dl class="summary-grid">
            <div v-for="item in summaryItems" :key="item.label">
              <dt>{{ item.label }}</dt>
              <dd>{{ item.value }}</dd>
            </div>
          </dl>
        </div>

        <div
          v-if="hasAvailableActions(detail.controls)"
          class="summary-actions"
          aria-label="任务操作"
        >
          <UiButton
            v-if="detail.controls.canPause"
            variant="secondary"
            size="sm"
            leading-icon="lucide:pause"
            :disabled="actionLoading"
            @click="openActionDialog('pause')"
          >
            暂停
          </UiButton>
          <UiButton
            v-if="detail.controls.canResume"
            variant="primary"
            size="sm"
            leading-icon="lucide:play"
            :disabled="actionLoading"
            @click="runAction('resume')"
          >
            继续
          </UiButton>
          <UiButton
            v-if="detail.controls.canTerminate"
            variant="secondary"
            size="sm"
            leading-icon="lucide:square"
            :disabled="actionLoading"
            @click="openActionDialog('terminate')"
          >
            终止
          </UiButton>
          <UiButton
            v-if="detail.controls.canCancel"
            variant="danger"
            size="sm"
            leading-icon="lucide:x-circle"
            :disabled="actionLoading"
            @click="openActionDialog('cancel')"
          >
            取消
          </UiButton>
        </div>
      </section>

      <InlineNotice
        v-if="error"
        tone="danger"
        title="操作未完成"
        :message="error"
      />

      <section class="sample-outcome" aria-label="样本统计">
        <div class="section-head">
          <div>
            <h2>样本统计</h2>
            <p>按成功、失败和异常拆分当前评测样本。</p>
          </div>
          <strong>{{ completionRate }}</strong>
        </div>

        <div class="sample-track" aria-hidden="true">
          <span
            v-for="segment in sampleSegments"
            :key="segment.label"
            :class="`sample-track__segment sample-track__segment--${segment.tone}`"
            :style="{ width: segment.width }"
          ></span>
        </div>

        <dl class="sample-grid">
          <div
            v-for="item in sampleStats"
            :key="item.label"
            class="sample-stat"
            :class="`sample-stat--${item.tone}`"
          >
            <dt>{{ item.label }}</dt>
            <dd>{{ item.value }}</dd>
          </div>
        </dl>
      </section>

      <section class="detail-section">
        <div class="section-head">
          <div>
            <h2>基础信息</h2>
            <p>提交、数据集和运行参数。</p>
          </div>
        </div>

        <div class="detail-groups">
          <section
            v-for="group in detailGroups"
            :key="group.title"
            class="detail-group"
          >
            <div class="detail-group__title">
              <AppIcon :icon="group.icon" />
              <h3>{{ group.title }}</h3>
            </div>
            <dl>
              <div v-for="item in group.items" :key="item.label">
                <dt>{{ item.label }}</dt>
                <dd :title="item.value">{{ item.value }}</dd>
              </div>
            </dl>
          </section>
        </div>
      </section>

      <EvaluationReportSection
        :report="report"
        :loading="reportLoading"
        :error="reportError"
        :state-text="reportStateText"
        @retry="loadReport"
      />

      <EvaluationEvidenceSection
        :detail="detail"
        :download-loading="downloadLoading"
        :download-error="downloadError"
        @download="downloadSampleDetails"
      />
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
import { formatDateTimeLabel } from "@/modules/dataset/lib/dataset-utils";
import EvaluationEvidenceSection from "@/modules/evaluation/components/EvaluationEvidenceSection.vue";
import EvaluationReportSection from "@/modules/evaluation/components/EvaluationReportSection.vue";
import { useEvaluationDetailPage } from "@/modules/evaluation/composables/useEvaluationDetailPage";
import {
  hasAvailableActions,
} from "@/modules/evaluation/lib/evaluation-status";
import UiButton from "@/shared/ui/actions/UiButton.vue";
import AppIcon from "@/shared/ui/branding/AppIcon.vue";
import StatusTag from "@/shared/ui/display/StatusTag.vue";
import ConfirmDialog from "@/shared/ui/feedback/ConfirmDialog.vue";
import InlineNotice from "@/shared/ui/feedback/InlineNotice.vue";
import PageStatePanel from "@/shared/ui/feedback/PageStatePanel.vue";
import PageHero from "@/shared/ui/page/PageHero.vue";

type DetailTone = "primary" | "success" | "warning" | "danger" | "neutral";

const {
  detail,
  loading,
  error,
  report,
  reportLoading,
  reportError,
  reportStateText,
  downloadLoading,
  downloadError,
  actionLoading,
  actionDialogVisible,
  actionDialogTitle,
  actionDialogMessage,
  actionDialogConfirmText,
  actionDialogDanger,
  loadDetail,
  loadReport,
  goBack,
  downloadSampleDetails,
  openActionDialog,
  runAction,
  confirmAction,
} = useEvaluationDetailPage();

const formatOptionalDateTime = (value?: string | null): string =>
  value ? formatDateTimeLabel(value) : "未返回";

const formatRate = (value: number): string => `${Math.round(value)}%`;

const resolveScoreTone = (score: number | null): DetailTone => {
  if (score === null) return "neutral";
  if (score >= 85) return "success";
  if (score >= 70) return "primary";
  if (score >= 55) return "warning";
  return "danger";
};

const scoreTone = computed<DetailTone>(() =>
  resolveScoreTone(detail.value?.score ?? null),
);

const primaryScore = computed(() =>
  detail.value?.finalReportAvailable && typeof detail.value.score === "number"
    ? detail.value.score.toFixed(1)
    : "--",
);

const scoreCaption = computed(() => {
  if (!detail.value?.finalReportAvailable) {
    return "报告未生成";
  }

  return detail.value.publicToLeaderboard ? "公开结果" : "私有结果";
});

const reportTagValue = computed(() => {
  if (!detail.value) {
    return "pending";
  }

  if (report.value) {
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

const summaryItems = computed(() => {
  if (!detail.value) {
    return [];
  }

  return [
    {
      label: "完成进度",
      value: `${detail.value.progress.percent}%`,
    },
    {
      label: "创建时间",
      value: formatDateTimeLabel(detail.value.createdAt),
    },
    {
      label: "开始时间",
      value: formatOptionalDateTime(detail.value.startedAt),
    },
    {
      label: "完成时间",
      value: formatOptionalDateTime(detail.value.finishedAt),
    },
  ];
});

const sampleBase = computed(() => {
  if (!detail.value) {
    return {
      total: 0,
      success: 0,
      failed: 0,
      error: 0,
      completed: 0,
    };
  }

  const summary = detail.value.sampleSummary;
  const total = summary?.total ?? detail.value.progress.totalSampleCount ?? 0;
  const completed = summary
    ? summary.success + summary.failed + summary.error
    : (detail.value.progress.completedSampleCount ?? 0);

  return {
    total,
    success: summary?.success ?? 0,
    failed: summary?.failed ?? 0,
    error: summary?.error ?? 0,
    completed,
  };
});

const completionRate = computed(() => {
  const total = sampleBase.value.total;
  return total > 0
    ? formatRate((sampleBase.value.completed / total) * 100)
    : "0%";
});

const sampleSegments = computed(() => {
  const total = Math.max(1, sampleBase.value.total);
  return [
    {
      label: "成功",
      tone: "success",
      width: `${(sampleBase.value.success / total) * 100}%`,
    },
    {
      label: "失败",
      tone: "danger",
      width: `${(sampleBase.value.failed / total) * 100}%`,
    },
    {
      label: "异常",
      tone: "warning",
      width: `${(sampleBase.value.error / total) * 100}%`,
    },
  ];
});

const sampleStats = computed(() => [
  { label: "总样本数", value: String(sampleBase.value.total), tone: "neutral" },
  { label: "成功", value: String(sampleBase.value.success), tone: "success" },
  { label: "失败", value: String(sampleBase.value.failed), tone: "danger" },
  { label: "异常", value: String(sampleBase.value.error), tone: "warning" },
  { label: "完成率", value: completionRate.value, tone: "primary" },
]);

const detailGroups = computed(() => {
  if (!detail.value) {
    return [];
  }

  return [
    {
      title: "提交信息",
      icon: "lucide:send",
      items: [
        { label: "提交方式", value: detail.value.submitMethod.toUpperCase() },
        {
          label: "排行榜可见性",
          value: detail.value.publicToLeaderboard ? "公开" : "私有",
        },
        { label: "当前状态", value: detail.value.progress.statusText },
      ],
    },
    {
      title: "数据集",
      icon: "lucide:database",
      items: [
        {
          label: "数据集",
          value: detail.value.datasetNames.join("、") || "未返回",
        },
        {
          label: "数据集数量",
          value: `${detail.value.datasetIds.length} 个`,
        },
      ],
    },
    {
      title: "运行参数",
      icon: "lucide:sliders-horizontal",
      items: [
        { label: "难度", value: String(detail.value.parameters.difficulty) },
        {
          label: "超时时间",
          value: `${detail.value.parameters.timeoutMinutes} 分钟`,
        },
        { label: "最大步骤", value: String(detail.value.parameters.maxSteps) },
      ],
    },
    {
      title: "报告信息",
      icon: "lucide:file-bar-chart-2",
      items: [
        {
          label: "报告生成时间",
          value: report.value?.generatedAt
            ? formatDateTimeLabel(report.value.generatedAt)
            : "未生成",
        },
        {
          label: "评分模型",
          value: report.value?.versions.scoreModelVersion ?? "未返回",
        },
      ],
    },
  ];
});
</script>

<style scoped lang="scss">
.detail-page {
  display: flex;
  flex-direction: column;
  gap: 1.6rem;
  padding-bottom: 2.5rem;
}

.summary-band,
.sample-outcome,
.detail-section {
  position: relative;
  padding-top: 1.65rem;
  border-top: 1px solid rgba(148, 163, 184, 0.18);
}

.summary-band::before,
.sample-outcome::before,
.detail-section::before {
  position: absolute;
  top: -1px;
  left: 0;
  width: 8rem;
  height: 1px;
  background: linear-gradient(90deg, #2563eb, rgba(37, 99, 235, 0));
  content: "";
}

.summary-band {
  display: grid;
  grid-template-columns: minmax(170px, 0.28fr) minmax(0, 1fr) auto;
  gap: 1.45rem;
  align-items: stretch;
  overflow: hidden;
  padding: 1.5rem 1.2rem 1.2rem;
  border: 1px solid rgba(148, 163, 184, 0.16);
  background:
    radial-gradient(circle at 3% 10%, rgba(37, 99, 235, 0.12), transparent 32%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.78), rgba(248, 250, 252, 0.42));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.86);
  animation: detail-section-enter var(--duration-fade-in) var(--ease-emphasized) both;
}

.score-display {
  display: flex;
  min-width: 0;
  flex-direction: column;
  justify-content: center;
  padding: 0.95rem 1rem;
  border-left: 4px solid #2563eb;
  background: rgba(255, 255, 255, 0.7);
}

.score-display span,
.score-display small,
.summary-grid dt,
.sample-stat dt,
.detail-group dt {
  color: var(--color-text-subtle);
  font-size: 0.8rem;
  font-weight: 800;
}

.score-display strong {
  margin-top: 0.2rem;
  color: var(--color-text-dark);
  font-size: clamp(2.55rem, 5.4vw, 4.65rem);
  font-variant-numeric: tabular-nums;
  font-weight: 900;
  letter-spacing: 0;
  line-height: 0.95;
  white-space: nowrap;
}

.score-display small {
  margin-top: 0.55rem;
}

.summary-band--success .score-display {
  border-color: #16a34a;
  box-shadow: inset 0 0 32px rgba(22, 163, 74, 0.08);
}

.summary-band--warning .score-display {
  border-color: #f59e0b;
  box-shadow: inset 0 0 32px rgba(245, 158, 11, 0.08);
}

.summary-band--danger .score-display {
  border-color: #dc2626;
  box-shadow: inset 0 0 32px rgba(220, 38, 38, 0.08);
}

.summary-band__main {
  min-width: 0;
  align-self: center;
}

.identity-line {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.55rem;
  min-width: 0;
}

.identity-line code {
  max-width: min(42vw, 520px);
  overflow: hidden;
  color: var(--color-text-dark);
  font-family: var(--font-mono, monospace);
  font-weight: 800;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.status-copy {
  margin: 0.75rem 0 0;
  color: var(--color-text-muted);
  line-height: 1.68;
}

.progress-line {
  overflow: hidden;
  height: 0.42rem;
  margin-top: 0.85rem;
  background: rgba(148, 163, 184, 0.16);
}

.progress-line span {
  display: block;
  height: 100%;
  background: var(--grad-progress);
  transition: width var(--duration-slow) var(--ease-emphasized);
}

.summary-grid,
.sample-grid {
  display: grid;
  gap: 0;
}

.summary-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin: 1rem 0 0;
}

.summary-grid div,
.sample-stat,
.detail-group dl div {
  min-width: 0;
  padding: 0.75rem 0.85rem 0.75rem 0;
  border-top: 1px solid rgba(148, 163, 184, 0.13);
}

.summary-grid dd,
.sample-stat dd,
.detail-group dd {
  margin: 0.34rem 0 0;
  color: var(--color-text-dark);
  font-weight: 800;
  line-height: 1.42;
}

.summary-actions {
  display: flex;
  flex-wrap: wrap;
  align-content: flex-start;
  justify-content: flex-end;
  gap: 0.55rem;
}

.sample-outcome,
.detail-section {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.section-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.section-head h2 {
  margin: 0;
  color: var(--color-text-dark);
  font-size: 1.18rem;
}

.section-head p {
  margin: 0.35rem 0 0;
  color: var(--color-text-subtle);
  line-height: 1.68;
}

.section-head > strong {
  color: var(--color-primary);
  font-size: 1.9rem;
  font-variant-numeric: tabular-nums;
  line-height: 1;
}

.sample-track {
  display: flex;
  overflow: hidden;
  height: 0.72rem;
  background: rgba(148, 163, 184, 0.15);
}

.sample-track__segment {
  min-width: 0;
  transition: width var(--duration-slow) var(--ease-emphasized);
}

.sample-track__segment--success {
  background: #16a34a;
}

.sample-track__segment--danger {
  background: #dc2626;
}

.sample-track__segment--warning {
  background: #f59e0b;
}

.sample-grid {
  grid-template-columns: repeat(5, minmax(0, 1fr));
}

.sample-stat {
  border-left: 3px solid transparent;
  padding-left: 0.75rem;
  transition:
    background var(--duration-base) var(--ease-standard),
    transform var(--duration-base) var(--ease-standard);
}

.sample-stat:hover {
  background: rgba(255, 255, 255, 0.58);
  transform: translateY(-1px);
}

.sample-stat dd {
  font-size: 1.44rem;
  font-variant-numeric: tabular-nums;
}

.sample-stat--success {
  border-left-color: #16a34a;
}

.sample-stat--danger {
  border-left-color: #dc2626;
}

.sample-stat--warning {
  border-left-color: #f59e0b;
}

.sample-stat--primary {
  border-left-color: #2563eb;
}

.sample-stat--neutral {
  border-left-color: rgba(100, 116, 139, 0.34);
}

.detail-groups {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 1.2rem;
}

.detail-group {
  min-width: 0;
  padding-top: 0.95rem;
  border-top: 1px solid rgba(148, 163, 184, 0.16);
}

.detail-group__title {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  color: var(--color-primary);
}

.detail-group__title h3 {
  margin: 0;
  color: var(--color-text-dark);
  font-size: 1rem;
}

.detail-group dl {
  margin: 0.55rem 0 0;
}

.detail-group dd {
  overflow-wrap: anywhere;
}

@keyframes detail-section-enter {
  from {
    opacity: 0;
    transform: translateY(10px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 1180px) {
  .summary-band {
    grid-template-columns: minmax(150px, 0.3fr) minmax(0, 1fr);
  }

  .summary-actions {
    grid-column: 1 / -1;
    justify-content: flex-start;
  }

  .detail-groups {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 860px) {
  .summary-band,
  .summary-grid,
  .sample-grid,
  .detail-groups {
    grid-template-columns: 1fr;
  }

  .identity-line code {
    max-width: 100%;
  }

  .summary-actions :deep(.ui-button) {
    width: 100%;
  }
}

@media (max-width: 640px) {
  .summary-band {
    padding-inline: 0.85rem;
  }

  .section-head {
    flex-direction: column;
  }
}

@media (prefers-reduced-motion: reduce) {
  .summary-band,
  .progress-line span,
  .sample-track__segment,
  .sample-stat {
    animation: none;
    transition: none;
  }

  .sample-stat:hover {
    transform: none;
  }
}
</style>
