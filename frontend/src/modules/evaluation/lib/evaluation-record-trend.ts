import { translateRuntimeMessage } from "@/app/i18n/runtime-translator";
import type {
  EvaluationRecord,
  EvaluationScoreTrend,
  EvaluationScoreTrendScope,
} from "@/shared/types/agent-types";

const toTrendScore = (score: number): number => Number(score.toFixed(1));

export const buildEvaluationTrendFromRecords = (
  records: EvaluationRecord[],
  scope: EvaluationScoreTrendScope,
): EvaluationScoreTrend => {
  const scoredRecords = records
    .filter(
      (record) =>
        record.finalReportAvailable && typeof record.score === "number",
    )
    .sort(
      (left, right) =>
        new Date(left.finishedAt ?? left.createdAt).getTime() -
        new Date(right.finishedAt ?? right.createdAt).getTime(),
    );
  const scopedRecords =
    scope === "recent10" ? scoredRecords.slice(-10) : scoredRecords;

  return {
    scope,
    defaultScope: "recent10",
    defaultView: "capability",
    views: {
      capability: {
        label: translateRuntimeMessage("evaluation.trend.capabilityView"),
        metrics: ["conservativeScore"],
      },
      risk: {
        label: translateRuntimeMessage("evaluation.trend.riskView"),
        metrics: ["conservativeScore"],
      },
    },
    items: scopedRecords.map((record) => ({
      evaluationId: record.evaluationId,
      agentName: record.agentName,
      createdAt: record.createdAt,
      finishedAt: record.finishedAt ?? null,
      scores: {
        conservativeScore: toTrendScore(record.score as number),
      },
    })),
  };
};
