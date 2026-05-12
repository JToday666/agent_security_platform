import { formatDateTimeLabel } from "@/modules/dataset/lib/dataset-utils";
import { getEvaluationLeaderboardStatus } from "@/modules/evaluation/lib/evaluation-record-filters";
import {
  type AppTranslator,
  translateRuntimeMessage,
} from "@/app/i18n/runtime-translator";
import type {
  EvaluationDetail,
  EvaluationReportPayload,
} from "@/shared/types/agent-types";
import type { AppIconName } from "@/shared/ui/branding/app-icon-registry";

export type EvaluationDetailTone =
  | "primary"
  | "success"
  | "warning"
  | "danger"
  | "neutral";

export interface EvaluationDetailTextItem {
  label: string;
  value: string;
}

export interface EvaluationSampleSegment {
  label: string;
  tone: "success" | "danger" | "warning";
  width: string;
}

export interface EvaluationSampleStat {
  label: string;
  value: string;
  tone: "neutral" | "success" | "danger" | "warning" | "primary";
}

export interface EvaluationDetailGroup {
  title: string;
  icon: AppIconName;
  items: EvaluationDetailTextItem[];
}

export type EvaluationReportTagValue = "available" | "pending" | "missing";

export interface EvaluationSampleBase {
  total: number;
  success: number;
  failed: number;
  error: number;
  completed: number;
}

const formatOptionalDateTime = (
  value?: string | null,
  t: AppTranslator = translateRuntimeMessage,
): string => (value ? formatDateTimeLabel(value) : t("evaluation.common.noReturn"));

const formatRate = (value: number): string => `${Math.round(value)}%`;

export const getLeaderboardStatusLabel = (
  detail: Pick<
    EvaluationDetail,
    "publicToLeaderboard" | "leaderboardDisplayMode"
  >,
  t: AppTranslator = translateRuntimeMessage,
): string => {
  const status = getEvaluationLeaderboardStatus(detail);
  if (status === "anonymous") return t("common.status.anonymous");
  if (status === "unranked") return t("common.status.rankedOut");
  return t("common.status.public");
};

export const resolveEvaluationScoreTone = (
  score: number | null,
): EvaluationDetailTone => {
  if (score === null) return "neutral";
  if (score >= 85) return "success";
  if (score >= 70) return "primary";
  if (score >= 55) return "warning";
  return "danger";
};

export const formatEvaluationPrimaryScore = (
  detail: EvaluationDetail,
): string =>
  detail.finalReportAvailable && typeof detail.score === "number"
    ? detail.score.toFixed(1)
    : "--";

export const getEvaluationScoreCaption = (
  detail: EvaluationDetail,
  t: AppTranslator = translateRuntimeMessage,
): string => {
  if (!detail.finalReportAvailable) {
    return t("evaluation.summary.scoreCaptionPending");
  }

  return getLeaderboardStatusLabel(detail, t);
};

export const getEvaluationReportTagValue = (
  detail: EvaluationDetail,
  report: EvaluationReportPayload | null,
): EvaluationReportTagValue => {
  if (report) {
    return "available";
  }

  if (
    detail.status === "completed" ||
    detail.status === "terminated" ||
    detail.status === "failed" ||
    detail.status === "canceled"
  ) {
    return "missing";
  }

  return "pending";
};

export const buildEvaluationSummaryItems = (
  detail: EvaluationDetail,
  t: AppTranslator = translateRuntimeMessage,
): EvaluationDetailTextItem[] => [
  {
    label: t("evaluation.summary.completion"),
    value: `${detail.progress.percent}%`,
  },
  {
    label: t("evaluation.summary.createdAt"),
    value: formatDateTimeLabel(detail.createdAt),
  },
  {
    label: t("evaluation.summary.startedAt"),
    value: formatOptionalDateTime(detail.startedAt, t),
  },
  {
    label: t("evaluation.summary.finishedAt"),
    value: formatOptionalDateTime(detail.finishedAt, t),
  },
];

export const buildEvaluationSampleBase = (
  detail: EvaluationDetail,
): EvaluationSampleBase => {
  const summary = detail.sampleSummary;
  const total = summary?.total ?? detail.progress.totalSampleCount ?? 0;
  const completed = summary
    ? summary.success + summary.failed + summary.error
    : (detail.progress.completedSampleCount ?? 0);

  return {
    total,
    success: summary?.success ?? 0,
    failed: summary?.failed ?? 0,
    error: summary?.error ?? 0,
    completed,
  };
};

export const getEvaluationCompletionRate = (
  sampleBase: EvaluationSampleBase,
): string =>
  sampleBase.total > 0
    ? formatRate((sampleBase.completed / sampleBase.total) * 100)
    : "0%";

export const buildEvaluationSampleSegments = (
  sampleBase: EvaluationSampleBase,
  t: AppTranslator = translateRuntimeMessage,
): EvaluationSampleSegment[] => {
  const total = Math.max(1, sampleBase.total);
  return [
    {
      label: t("evaluation.outcomes.success"),
      tone: "success",
      width: `${(sampleBase.success / total) * 100}%`,
    },
    {
      label: t("evaluation.outcomes.failed"),
      tone: "danger",
      width: `${(sampleBase.failed / total) * 100}%`,
    },
    {
      label: t("evaluation.outcomes.error"),
      tone: "warning",
      width: `${(sampleBase.error / total) * 100}%`,
    },
  ];
};

export const buildEvaluationSampleStats = (
  sampleBase: EvaluationSampleBase,
  completionRate: string,
  t: AppTranslator = translateRuntimeMessage,
): EvaluationSampleStat[] => [
  {
    label: t("evaluation.summary.totalSamples"),
    value: String(sampleBase.total),
    tone: "neutral",
  },
  {
    label: t("evaluation.outcomes.success"),
    value: String(sampleBase.success),
    tone: "success",
  },
  {
    label: t("evaluation.outcomes.failed"),
    value: String(sampleBase.failed),
    tone: "danger",
  },
  {
    label: t("evaluation.outcomes.error"),
    value: String(sampleBase.error),
    tone: "warning",
  },
  {
    label: t("evaluation.metrics.completionRate.label"),
    value: completionRate,
    tone: "primary",
  },
];

export const buildEvaluationDetailGroups = (
  detail: EvaluationDetail,
  report: EvaluationReportPayload | null,
  t: AppTranslator = translateRuntimeMessage,
): EvaluationDetailGroup[] => [
  {
    title: t("evaluation.sections.submit"),
    icon: "app:evaluation.submit",
    items: [
      { label: t("evaluation.summary.submitMethod"), value: detail.submitMethod.toUpperCase() },
      {
        label: t("evaluation.summary.leaderboardStatus"),
        value: getLeaderboardStatusLabel(detail, t),
      },
      { label: t("evaluation.summary.currentStatus"), value: detail.progress.statusText },
    ],
  },
  {
    title: t("evaluation.sections.dataset"),
    icon: "app:dataset.catalog",
    items: [
      {
        label: t("evaluation.summary.datasets"),
        value:
          detail.datasetNames.join(t("evaluation.common.listSeparator")) ||
          t("evaluation.common.noReturn"),
      },
      {
        label: t("evaluation.summary.datasetCount"),
        value: t("evaluation.summary.datasetCountValue", {
          count: detail.datasetIds.length,
        }),
      },
    ],
  },
  {
    title: t("evaluation.sections.runParameters"),
    icon: "app:evaluation.runParameters",
    items: [
      { label: t("evaluation.summary.difficulty"), value: String(detail.parameters.difficulty) },
      {
        label: t("evaluation.summary.timeout"),
        value: t("evaluation.summary.timeoutValue", {
          value: detail.parameters.timeoutMinutes,
        }),
      },
      { label: t("evaluation.summary.maxSteps"), value: String(detail.parameters.maxSteps) },
    ],
  },
  {
    title: t("evaluation.sections.report"),
    icon: "app:evaluation.report",
    items: [
      {
        label: t("evaluation.summary.reportGeneratedAt"),
        value: report?.generatedAt
          ? formatDateTimeLabel(report.generatedAt)
          : t("evaluation.common.notGenerated"),
      },
      {
        label: t("evaluation.summary.scoreModel"),
        value: report?.versions.scoreModelVersion ?? t("evaluation.common.noReturn"),
      },
    ],
  },
];
