import { describe, expect, it } from "vitest";
import {
  buildSampleScatterOption,
  buildTrendLineOption,
} from "@/modules/evaluation/lib/evaluation-report-chart-options";
import type {
  EvaluationReportPayload,
  EvaluationScoreTrend,
} from "@/shared/types/agent-types";

const t = (key: string, params?: Record<string, unknown>): string => {
  const templateByKey: Record<string, string> = {
    "evaluation.charts.completionDate": "Completed: {date}",
    "evaluation.charts.evaluationId": "Evaluation: {id}",
    "evaluation.charts.sampleTooltip":
      "Difficulty: {difficulty}<br/>Duration: {duration} ms<br/>Sample: {sampleId}",
  };
  const template = templateByKey[key] ?? key;

  if (!params) {
    return template;
  }

  return Object.entries(params).reduce(
    (message, [name, value]) =>
      message.replaceAll(`{${name}}`, String(value ?? "")),
    template,
  );
};

const createReport = (): EvaluationReportPayload => ({
  evaluationId: "eval_1",
  status: "completed",
  generatedAt: "2026-05-01T00:00:00.000Z",
  scores: {
    conservativeScore: 80,
    performanceScore: 82,
    confidence: 75,
    completionScore: 90,
    safetyScore: 88,
    hardScore: 70,
    unsafeRate: 5,
    timeScore: 76,
  },
  rawStats: {
    total: 1,
    success: 1,
    failed: 0,
    error: 0,
    completionRate: 1,
    successRate: 1,
    conditionalSuccessRate: 1,
  },
  posteriorInterval: {
    psQ05: 70,
    psQ50: 80,
    psQ95: 90,
  },
  coverage: {
    difficultyBucketHitCount: 1,
    difficultyCoverageRatio: 1,
  },
  breakdowns: {
    outcomeSummary: {
      total: 1,
      success: 1,
      failed: 0,
      error: 0,
    },
    difficultyBuckets: [],
    datasetSummaries: [],
    sampleScatterPoints: [
      {
        sampleId: "<img src=x onerror=alert(1)>",
        difficulty: 0.5,
        durationMs: 120,
        normalizedResult: "success",
      },
    ],
  },
  versions: {
    difficultyVersion: "v1",
    scoreModelVersion: "v1",
    benchmarkVersion: "v1",
  },
});

const getTooltipFormatter = (
  tooltip: unknown,
): ((params: unknown) => string) => {
  const tooltipOption = Array.isArray(tooltip) ? tooltip[0] : tooltip;
  return (tooltipOption as { formatter?: (params: unknown) => string })
    .formatter as (params: unknown) => string;
};

describe("evaluation report chart options", () => {
  it("escapes dynamic HTML in trend tooltip output", () => {
    const trend: EvaluationScoreTrend = {
      scope: "recent10",
      defaultScope: "recent10",
      defaultView: "capability",
      views: {
        capability: {
          label: "Capability",
          metrics: ["conservativeScore"],
        },
        risk: {
          label: "Risk",
          metrics: ["unsafeRate"],
        },
      },
      items: [
        {
          evaluationId: "eval_<script>",
          agentName: "<img src=x onerror=alert(1)>",
          createdAt: "2026-05-01T00:00:00.000Z",
          finishedAt: "2026-05-02T00:00:00.000Z",
          scores: {
            conservativeScore: 88,
          },
        },
      ],
    };
    const option = buildTrendLineOption(trend, "capability", t);
    const formatter = getTooltipFormatter(option.tooltip);

    const html = formatter([
      {
        dataIndex: 0,
        marker: '<span class="marker"></span>',
        seriesName: "Metric <strong>",
        value: 88,
      },
    ]);

    expect(html).toContain("&lt;img src=x onerror=alert(1)&gt;");
    expect(html).toContain("eval_&lt;script&gt;");
    expect(html).toContain("Metric &lt;strong&gt;");
    expect(html).not.toContain("<img src=x");
  });

  it("escapes dynamic HTML in sample scatter tooltip output", () => {
    const option = buildSampleScatterOption(createReport(), t);
    const formatter = getTooltipFormatter(option.tooltip);

    const html = formatter({
      value: [0.5, 120, "<img src=x onerror=alert(1)>"],
    });

    expect(html).toContain("&lt;img src=x onerror=alert(1)&gt;");
    expect(html).not.toContain("<img src=x");
  });
});
