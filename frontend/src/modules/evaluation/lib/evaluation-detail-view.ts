import { formatDateTimeLabel } from "@/modules/dataset/lib/dataset-utils";
import type {
  EvaluationDetail,
  EvaluationReportPayload,
} from "@/shared/types/agent-types";

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
  icon: string;
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

const formatOptionalDateTime = (value?: string | null): string =>
  value ? formatDateTimeLabel(value) : "未返回";

const formatRate = (value: number): string => `${Math.round(value)}%`;

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

export const getEvaluationScoreCaption = (detail: EvaluationDetail): string => {
  if (!detail.finalReportAvailable) {
    return "报告未生成";
  }

  return detail.publicToLeaderboard ? "公开结果" : "私有结果";
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
): EvaluationDetailTextItem[] => [
  {
    label: "完成进度",
    value: `${detail.progress.percent}%`,
  },
  {
    label: "创建时间",
    value: formatDateTimeLabel(detail.createdAt),
  },
  {
    label: "开始时间",
    value: formatOptionalDateTime(detail.startedAt),
  },
  {
    label: "完成时间",
    value: formatOptionalDateTime(detail.finishedAt),
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
): EvaluationSampleSegment[] => {
  const total = Math.max(1, sampleBase.total);
  return [
    {
      label: "成功",
      tone: "success",
      width: `${(sampleBase.success / total) * 100}%`,
    },
    {
      label: "失败",
      tone: "danger",
      width: `${(sampleBase.failed / total) * 100}%`,
    },
    {
      label: "异常",
      tone: "warning",
      width: `${(sampleBase.error / total) * 100}%`,
    },
  ];
};

export const buildEvaluationSampleStats = (
  sampleBase: EvaluationSampleBase,
  completionRate: string,
): EvaluationSampleStat[] => [
  { label: "总样本数", value: String(sampleBase.total), tone: "neutral" },
  { label: "成功", value: String(sampleBase.success), tone: "success" },
  { label: "失败", value: String(sampleBase.failed), tone: "danger" },
  { label: "异常", value: String(sampleBase.error), tone: "warning" },
  { label: "完成率", value: completionRate, tone: "primary" },
];

export const buildEvaluationDetailGroups = (
  detail: EvaluationDetail,
  report: EvaluationReportPayload | null,
): EvaluationDetailGroup[] => [
  {
    title: "提交信息",
    icon: "lucide:send",
    items: [
      { label: "提交方式", value: detail.submitMethod.toUpperCase() },
      {
        label: "排行榜可见性",
        value: detail.publicToLeaderboard ? "公开" : "私有",
      },
      { label: "当前状态", value: detail.progress.statusText },
    ],
  },
  {
    title: "数据集",
    icon: "lucide:database",
    items: [
      {
        label: "数据集",
        value: detail.datasetNames.join("、") || "未返回",
      },
      {
        label: "数据集数量",
        value: `${detail.datasetIds.length} 个`,
      },
    ],
  },
  {
    title: "运行参数",
    icon: "lucide:sliders-horizontal",
    items: [
      { label: "难度", value: String(detail.parameters.difficulty) },
      {
        label: "超时时间",
        value: `${detail.parameters.timeoutMinutes} 分钟`,
      },
      { label: "最大步骤", value: String(detail.parameters.maxSteps) },
    ],
  },
  {
    title: "报告信息",
    icon: "lucide:file-bar-chart-2",
    items: [
      {
        label: "报告生成时间",
        value: report?.generatedAt
          ? formatDateTimeLabel(report.generatedAt)
          : "未生成",
      },
      {
        label: "评分模型",
        value: report?.versions.scoreModelVersion ?? "未返回",
      },
    ],
  },
];
