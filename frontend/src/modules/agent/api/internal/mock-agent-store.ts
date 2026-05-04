import { STORAGE_KEYS } from "@/shared/constants/storage-keys";
import type {
  AgentCreatePayload,
  AgentDetail,
  AgentListItem,
  AgentStatus,
  AgentTemplate,
  AgentVerifyResponse,
} from "@/shared/types/agent-registry-types";

const nowIso = (): string => new Date().toISOString();

export const referenceAgentTemplates: AgentTemplate[] = [
  {
    templateId: "http_submit_poll_basic",
    name: "提交 + 轮询 Agent",
    description: "适用于先提交任务，再通过运行 ID 轮询结果的 Agent。",
    recommended: true,
    sortOrder: 10,
    level: "basic",
    tags: ["推荐", "异步", "轮询"],
    defaultConfig: {
      invokeMode: "submit_poll",
      connection: {
        baseUrl: "",
        invokePath: "/api/runs",
        resultPathTemplate: "/api/runs/{externalRunId}",
        requestTimeoutSeconds: 30,
        pollIntervalSeconds: 2,
        pollTimeoutSeconds: 300,
      },
      auth: {
        type: "bearer",
        config: {
          token: "",
        },
      },
      platformInputMapping: {
        task: "task",
        entryUrl: "entryUrl",
        timeoutSeconds: "timeoutSeconds",
        sampleId: "sampleId",
        evaluationId: "evaluationId",
        maxSteps: "maxSteps",
      },
      taskRenderMode: "goal_only",
      customRequestBody: {},
      requestOptions: {
        structuredOutput: {
          supported: true,
          fieldAlias: "outputSchema",
        },
      },
      platformOutputMapping: {
        externalRunId: "data.runId",
        status: "data.status",
        finalAnswer: "data.answer",
        errorMessage: "data.error.message",
        stepCount: "data.metrics.stepCount",
        artifacts: "data.artifacts",
      },
      terminalStatuses: ["completed", "failed", "timed_out"],
      successStatuses: ["completed"],
    },
  },
];

const referenceAgents: AgentDetail[] = [
  {
    agentId: "agt_active_skyvern",
    templateId: "http_submit_poll_basic",
    name: "Skyvern Agent",
    description: "通过 API 执行 Web 自动化任务。",
    invokeMode: "submit_poll",
    status: "active",
    connection: {
      baseUrl: "https://api.agent.example.com",
      invokePath: "/v1/run/tasks",
      resultPathTemplate: "/v1/run/tasks/{externalRunId}",
      requestTimeoutSeconds: 30,
      pollIntervalSeconds: 2,
      pollTimeoutSeconds: 300,
    },
    auth: {
      type: "api_key_header",
      hasCredential: true,
      publicConfig: {
        headerName: "x-api-key",
        hasSecret: true,
      },
    },
    platformInputMapping: {
      task: "prompt",
      entryUrl: "url",
      timeoutSeconds: "timeout_sec",
      sampleId: "case_id",
      evaluationId: "job_id",
      maxSteps: "max_steps",
    },
    taskRenderMode: "goal_only",
    customRequestBody: {
      engine: "skyvern-2.0",
    },
    requestOptions: {
      structuredOutput: {
        supported: true,
        fieldAlias: "data_extraction_schema",
      },
    },
    platformOutputMapping: {
      externalRunId: "task_id",
      status: "status",
      finalAnswer: "result.answer",
      errorMessage: "error.message",
      stepCount: "metrics.step_count",
      artifacts: "artifacts",
    },
    terminalStatuses: ["completed", "failed", "timed_out"],
    successStatuses: ["completed"],
    verifiedAt: "2026-04-27T08:10:00Z",
    lastVerification: {
      passed: true,
      warnings: [],
      errors: [],
    },
    actions: {
      canSubmitEvaluation: true,
      canVerify: true,
      canArchive: true,
      canCopyCreate: true,
    },
    createdAt: "2026-04-27T08:00:00Z",
    updatedAt: "2026-04-27T08:10:00Z",
  },
  {
    agentId: "agt_draft_browser",
    templateId: "http_submit_poll_basic",
    name: "Browser Runner",
    description: "待验证的浏览器执行 Agent。",
    invokeMode: "submit_poll",
    status: "draft",
    connection: {
      baseUrl: "https://browser-agent.example.com",
      invokePath: "/runs",
      resultPathTemplate: "/runs/{externalRunId}",
      requestTimeoutSeconds: 30,
      pollIntervalSeconds: 2,
      pollTimeoutSeconds: 300,
    },
    auth: {
      type: "bearer",
      hasCredential: true,
      publicConfig: {
        hasToken: true,
      },
    },
    platformInputMapping: {
      task: "task",
      entryUrl: "entryUrl",
      timeoutSeconds: "timeoutSeconds",
      sampleId: "sampleId",
      evaluationId: "evaluationId",
      maxSteps: "maxSteps",
    },
    taskRenderMode: "goal_only",
    customRequestBody: {},
    requestOptions: {
      structuredOutput: {
        supported: true,
        fieldAlias: "outputSchema",
      },
    },
    platformOutputMapping: {
      externalRunId: "data.runId",
      status: "data.status",
      finalAnswer: "data.answer",
      errorMessage: "data.error.message",
    },
    terminalStatuses: ["completed", "failed", "timed_out"],
    successStatuses: ["completed"],
    verifiedAt: null,
    lastVerification: null,
    actions: {
      canSubmitEvaluation: false,
      canVerify: true,
      canArchive: true,
      canCopyCreate: true,
    },
    createdAt: "2026-04-26T06:30:00Z",
    updatedAt: "2026-04-26T06:30:00Z",
  },
  {
    agentId: "agt_invalid_ops",
    templateId: "http_submit_poll_basic",
    name: "Ops Control Agent",
    description: "最近一次验证未通过的执行 Agent。",
    invokeMode: "submit_poll",
    status: "invalid",
    connection: {
      baseUrl: "https://ops-agent.example.com",
      invokePath: "/tasks",
      resultPathTemplate: "/tasks/{externalRunId}",
      requestTimeoutSeconds: 30,
      pollIntervalSeconds: 2,
      pollTimeoutSeconds: 300,
    },
    auth: {
      type: "custom_header",
      hasCredential: true,
      publicConfig: {
        headerName: "X-Agent-Token",
        hasSecret: true,
      },
    },
    platformInputMapping: {
      task: "prompt",
      entryUrl: "url",
      timeoutSeconds: "timeout_sec",
      sampleId: "sample_id",
      evaluationId: "evaluation_id",
      maxSteps: "max_steps",
    },
    taskRenderMode: "goal_only",
    customRequestBody: {
      run_with: "agent",
    },
    requestOptions: {
      structuredOutput: {
        supported: true,
        fieldAlias: "outputSchema",
      },
    },
    platformOutputMapping: {
      externalRunId: "data.id",
      status: "data.state",
      finalAnswer: "data.answer",
      errorMessage: "error.message",
    },
    terminalStatuses: ["completed", "failed", "timed_out"],
    successStatuses: ["completed"],
    verifiedAt: "2026-04-26T07:00:00Z",
    lastVerification: {
      passed: false,
      warnings: [],
      errors: [
        {
          code: "OUTPUT_MAPPING_NOT_FOUND",
          message: "未能从响应路径 data.id 解析 externalRunId。",
        },
      ],
    },
    actions: {
      canSubmitEvaluation: false,
      canVerify: true,
      canArchive: true,
      canCopyCreate: true,
    },
    createdAt: "2026-04-25T09:20:00Z",
    updatedAt: "2026-04-26T07:00:00Z",
  },
];

const clone = <T>(value: T): T => JSON.parse(JSON.stringify(value)) as T;

const computeActions = (status: AgentStatus): AgentDetail["actions"] => ({
  canSubmitEvaluation: status === "active",
  canVerify: status === "draft" || status === "active" || status === "invalid",
  canArchive: status === "draft" || status === "active" || status === "invalid",
  canCopyCreate: true,
});

const readStoredAgents = (): AgentDetail[] | null => {
  const raw = localStorage.getItem(STORAGE_KEYS.mock.agents);
  if (!raw) {
    return null;
  }

  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? (parsed as AgentDetail[]) : null;
  } catch {
    return null;
  }
};

export const getStoredMockAgents = (): AgentDetail[] => {
  const storedAgents = readStoredAgents();
  if (storedAgents) {
    return storedAgents.map((agent) => ({
      ...agent,
      actions: computeActions(agent.status),
    }));
  }

  const initialAgents = clone(referenceAgents);
  writeStoredMockAgents(initialAgents);
  return initialAgents;
};

export const writeStoredMockAgents = (agents: AgentDetail[]) => {
  localStorage.setItem(STORAGE_KEYS.mock.agents, JSON.stringify(agents));
};

export const toAgentListItem = (agent: AgentDetail): AgentListItem => ({
  agentId: agent.agentId,
  name: agent.name,
  description: agent.description,
  invokeMode: agent.invokeMode,
  status: agent.status,
  verifiedAt: agent.verifiedAt,
  lastVerificationPassed: agent.lastVerification?.passed ?? null,
  canSubmitEvaluation: agent.status === "active",
  canVerify: computeActions(agent.status).canVerify,
  canArchive: computeActions(agent.status).canArchive,
  canCopyCreate: true,
  createdAt: agent.createdAt,
  updatedAt: agent.updatedAt,
});

export const getStoredMockAgentById = (agentId: string): AgentDetail | null =>
  getStoredMockAgents().find((agent) => agent.agentId === agentId) ?? null;

export const createStoredMockAgent = (
  payload: AgentCreatePayload,
): AgentDetail => {
  const createdAt = nowIso();
  const agent: AgentDetail = {
    ...payload,
    agentId: `agt_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
    status: "draft",
    auth: {
      type: payload.auth.type,
      hasCredential: payload.auth.type !== "none",
      publicConfig:
        payload.auth.type === "api_key_header" ||
        payload.auth.type === "custom_header"
          ? {
              headerName: payload.auth.config.headerName,
              hasSecret: Boolean(payload.auth.config.secret),
            }
          : {
              hasToken: Boolean(payload.auth.config.token),
            },
    },
    verifiedAt: null,
    lastVerification: null,
    actions: computeActions("draft"),
    createdAt,
    updatedAt: createdAt,
  };
  const nextAgents = [agent, ...getStoredMockAgents()];
  writeStoredMockAgents(nextAgents);
  return agent;
};

export const updateStoredMockAgent = (nextAgent: AgentDetail) => {
  const nextAgents = getStoredMockAgents().map((agent) =>
    agent.agentId === nextAgent.agentId
      ? { ...nextAgent, actions: computeActions(nextAgent.status) }
      : agent,
  );
  writeStoredMockAgents(nextAgents);
};

export const verifyStoredMockAgent = (agentId: string): AgentVerifyResponse => {
  const agent = getStoredMockAgentById(agentId);
  if (!agent) {
    throw new Error("Agent 不存在。");
  }

  const verifiedAt = nowIso();
  const passed = !agent.name.includes("失败");
  const response: AgentVerifyResponse = {
    agentId,
    passed,
    status: passed ? "active" : "invalid",
    verifiedAt,
    warnings:
      agent.connection.pollTimeoutSeconds > 240
        ? [
            {
              code: "POLL_TIMEOUT_LONG",
              message: "轮询总超时时间较长，可能影响评测吞吐。",
            },
          ]
        : [],
    errors: passed
      ? []
      : [
          {
            code: "MOCK_VERIFY_FAILED",
            message: "请检查输出字段映射后重新验证。",
          },
        ],
  };

  updateStoredMockAgent({
    ...agent,
    status: response.status,
    verifiedAt,
    lastVerification: {
      passed: response.passed,
      warnings: response.warnings,
      errors: response.errors,
    },
    updatedAt: verifiedAt,
  });

  return response;
};
