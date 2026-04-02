import request from "@/utils/Request";
import { ApiConfig } from "@/api/Config";
import { STORAGE_KEYS } from "@/constants/StorageKeys";
import type {
  EvaluationDetail,
  EvaluationMetric,
  EvaluationRecord,
  PrecheckResponse,
  SubmitAgentPayload,
  SubmitMetaApiResponse,
  SubmitMetaResponse,
  SubmitResponse,
} from "@/types/AgentTypes";
import {
  createErrorEnvelope,
  createSuccessEnvelope,
  resolveMockEnvelope,
} from "@/api/MockApiUtils";
import {
  buildSubmitAgentApiPayload,
  normalizeSubmitMeta,
} from "@/api/adapters/DatasetAdapters";
import {
  getReferenceDatasetIds,
  getReferenceDatasetNameMap,
  referenceEvaluationRecords,
  referenceSubmitMeta,
} from "@/api/fixtures/DatasetFixtures";
import { validateSubmitPayload } from "@/utils/submit";

interface StoredEvaluationRecord extends EvaluationRecord {
  requestId: string;
}

const MOCK_COMPLETION_DELAY_MS = 4000;
const useLiveSubmissionApi = ApiConfig.submission.useLive;
const useLiveReferenceApi = ApiConfig.reference.useLive;
const referenceDatasetNameMap = getReferenceDatasetNameMap();

const readStoredRecords = (): StoredEvaluationRecord[] => {
  try {
    const raw = localStorage.getItem(STORAGE_KEYS.mock.evaluations);
    if (!raw) {
      return [];
    }

    return JSON.parse(raw) as StoredEvaluationRecord[];
  } catch {
    return [];
  }
};

const writeStoredRecords = (records: StoredEvaluationRecord[]): void => {
  localStorage.setItem(STORAGE_KEYS.mock.evaluations, JSON.stringify(records));
};

const nowIso = (): string => new Date().toISOString();

const computeScore = (record: EvaluationRecord): number => {
  const datasetFactor = record.datasetIds.length * 1.8;
  const retryPenalty = record.parameters.retryEnabled ? 1.5 : 0;
  const difficultyBonus = record.parameters.difficulty * 7;
  const timeoutBonus = Math.min(record.parameters.timeoutMinutes, 24) * 0.18;
  const seed = record.agentName.length + record.evaluationId.length;
  const score =
    82 +
    datasetFactor +
    difficultyBonus +
    timeoutBonus -
    retryPenalty +
    (seed % 4);

  return Number(Math.min(98.8, Math.max(76.4, score)).toFixed(1));
};

const buildMetrics = (record: EvaluationRecord): EvaluationMetric[] => {
  const score = record.score ?? computeScore(record);
  const attackDetection = Math.min(99, Math.round(score + 2));
  const policyStability = Math.min(
    97,
    Math.round(score - (record.parameters.retryEnabled ? 1 : 0)),
  );
  const executionBoundary = Math.min(
    98,
    Math.round(score + (record.submitMethod === "docker" ? 1 : 0)),
  );
  const responseSpeed = Math.max(
    68,
    Math.round(96 - record.parameters.timeoutMinutes * 0.9),
  );

  return [
    {
      name: "攻击检测率",
      value: `${attackDetection}%`,
      percentage: attackDetection,
      description: "识别恶意提示与异常工具响应的能力。",
    },
    {
      name: "策略稳定性",
      value: `${policyStability}%`,
      percentage: policyStability,
      description: "多轮攻击下仍保持安全边界的稳定程度。",
    },
    {
      name: "执行边界控制",
      value: `${executionBoundary}%`,
      percentage: executionBoundary,
      description: "面向越权调用和高风险动作的阻断能力。",
    },
    {
      name: "响应效率",
      value: `${responseSpeed}%`,
      percentage: responseSpeed,
      description: "在安全判定与服务时延之间的平衡表现。",
    },
  ];
};

const upgradeStoredRecords = (
  records: StoredEvaluationRecord[],
): StoredEvaluationRecord[] => {
  let changed = false;

  const upgraded = records.map<StoredEvaluationRecord>((record) => {
    if (record.status === "completed") {
      return record;
    }

    const elapsed = Date.now() - new Date(record.createdAt).getTime();
    if (elapsed < MOCK_COMPLETION_DELAY_MS) {
      return record;
    }

    changed = true;
    return {
      ...record,
      status: "completed",
      updatedAt: nowIso(),
      score: computeScore(record),
    };
  });

  if (changed) {
    writeStoredRecords(upgraded);
  }

  return upgraded;
};

const getMergedRecords = (): EvaluationRecord[] => {
  const storedRecords = upgradeStoredRecords(readStoredRecords());

  return [...storedRecords, ...referenceEvaluationRecords].sort(
    (left, right) =>
      new Date(right.createdAt).getTime() - new Date(left.createdAt).getTime(),
  );
};

const buildEvaluationDetail = (record: EvaluationRecord): EvaluationDetail => ({
  ...record,
  summary:
    record.status === "completed"
      ? `本次评测共覆盖 ${record.datasetNames.length} 个评测项，核心安全指标表现稳定，建议结合详细指标继续优化高风险边界。`
      : "任务已创建，系统正在调度评测节点与评测项执行队列，请稍后刷新查看结果。",
  warnings:
    record.status === "completed"
      ? record.parameters.retryEnabled
        ? ["已启用失败重试，建议复核长耗时场景下的重试副作用。"]
        : []
      : ["评测尚未完成，当前展示的是任务创建信息与预计执行范围。"],
  metrics:
    record.status === "completed"
      ? buildMetrics(record)
      : [
          {
            name: "任务创建",
            value: "100%",
            percentage: 100,
            description: "任务已成功入队，等待评测执行。",
          },
          {
            name: "执行准备",
            value: "65%",
            percentage: 65,
            description: "目录装载与环境校验已完成，正在分配执行资源。",
          },
        ],
});

const getReferenceMeta = async (): Promise<SubmitMetaResponse> => {
  if (useLiveReferenceApi) {
    const response = await request.get<SubmitMetaApiResponse>(
      "/agents/submit-meta",
    );

    if (!response.success || !response.data) {
      throw new Error(response.message || "提交元数据加载失败。");
    }

    return normalizeSubmitMeta(response.data);
  }

  const result = await resolveMockEnvelope(
    createSuccessEnvelope(referenceSubmitMeta),
  );
  return result.data;
};

export const getSubmitMeta = async (): Promise<SubmitMetaResponse> =>
  getReferenceMeta();

export const precheckAgent = async (
  payload: SubmitAgentPayload,
): Promise<PrecheckResponse> => {
  if (useLiveSubmissionApi) {
    const response = await request.post<PrecheckResponse>(
      "/agents/precheck",
      buildSubmitAgentApiPayload(payload),
    );

    if (!response.success || !response.data) {
      throw new Error(response.message || "预检查失败。");
    }

    return response.data;
  }

  const meta = await getReferenceMeta();
  const validation = validateSubmitPayload(
    payload,
    meta,
    getReferenceDatasetIds(),
  );

  if (!validation.valid) {
    const result = await resolveMockEnvelope(
      createErrorEnvelope(40002, validation.errors[0] || "参数校验失败。", {
        ok: false,
        warnings: validation.errors,
      }),
    );
    throw new Error(result.message);
  }

  const warnings: string[] = [];
  if (payload.publicToLeaderboard) {
    warnings.push("该次结果将进入公开排行榜，请确认描述中不包含敏感信息。");
  }

  const recommendedMax = meta.timeoutMinutes.recommendedMax ?? 20;
  if (payload.parameters.timeoutMinutes > recommendedMax) {
    warnings.push(
      `当前超时时间高于建议值 ${recommendedMax}，评测排队与执行耗时可能更长。`,
    );
  }

  const result = await resolveMockEnvelope(
    createSuccessEnvelope({
      ok: true,
      warnings,
    }),
  );

  return result.data;
};

export const submitAgent = async (
  payload: SubmitAgentPayload,
): Promise<SubmitResponse> => {
  if (useLiveSubmissionApi) {
    const response = await request.post<SubmitResponse>(
      "/agents/submit",
      buildSubmitAgentApiPayload(payload),
    );

    if (!response.success || !response.data) {
      throw new Error(response.message || "提交失败，请稍后重试。");
    }

    return response.data;
  }

  const meta = await getReferenceMeta();
  const validation = validateSubmitPayload(
    payload,
    meta,
    getReferenceDatasetIds(),
  );

  if (!validation.valid) {
    const result = await resolveMockEnvelope(
      createErrorEnvelope(40002, validation.errors[0] || "参数校验失败。", {
        evaluationId: "",
        status: "pending",
        createdAt: "",
      }),
      { delay: 520 },
    );
    throw new Error(result.message);
  }

  const existing = readStoredRecords().find(
    (record) => record.requestId === payload.requestId,
  );
  if (existing) {
    const result = await resolveMockEnvelope(
      createSuccessEnvelope({
        evaluationId: existing.evaluationId,
        status: existing.status,
        createdAt: existing.createdAt,
      }),
      { delay: 520 },
    );
    return result.data;
  }

  const now = nowIso();
  const record: StoredEvaluationRecord = {
    evaluationId: `eval_${Date.now()}`,
    requestId: payload.requestId,
    agentName: payload.agentName.trim(),
    description: payload.description?.trim(),
    createdAt: now,
    updatedAt: now,
    status: "pending",
    publicToLeaderboard: payload.publicToLeaderboard,
    datasetIds: payload.selectedDatasetIds,
    datasetNames: payload.selectedDatasetIds.map(
      (item) => referenceDatasetNameMap.get(item) ?? item,
    ),
    submitMethod: payload.submitMethod,
    score: undefined,
    ownerName: "当前用户",
    parameters: payload.parameters,
  };

  writeStoredRecords([record, ...readStoredRecords()]);

  const result = await resolveMockEnvelope(
    createSuccessEnvelope({
      evaluationId: record.evaluationId,
      status: record.status,
      createdAt: record.createdAt,
    }),
    { delay: 780 },
  );

  return result.data;
};

export const getEvaluationRecords = async (): Promise<EvaluationRecord[]> => {
  if (useLiveSubmissionApi) {
    const response = await request.get<EvaluationRecord[]>("/evaluations");

    if (!response.success || !response.data) {
      throw new Error(response.message || "评测记录加载失败。");
    }

    return response.data;
  }

  const result = await resolveMockEnvelope(
    createSuccessEnvelope(getMergedRecords()),
  );
  return result.data;
};

export const getEvaluationDetail = async (
  evaluationId: string,
): Promise<EvaluationDetail> => {
  if (useLiveSubmissionApi) {
    const response = await request.get<EvaluationDetail>(
      `/evaluations/${evaluationId}`,
    );

    if (!response.success || !response.data) {
      throw new Error(response.message || "评测详情加载失败。");
    }

    return response.data;
  }

  const record = getMergedRecords().find(
    (item) => item.evaluationId === evaluationId,
  );

  if (!record) {
    const result = await resolveMockEnvelope(
      createErrorEnvelope(40400, "评测记录不存在。", null),
    );
    throw new Error(result.message);
  }

  const result = await resolveMockEnvelope(
    createSuccessEnvelope(buildEvaluationDetail(record)),
  );

  return result.data;
};
