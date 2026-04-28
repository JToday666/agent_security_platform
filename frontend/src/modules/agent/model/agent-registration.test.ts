import { describe, expect, it } from "vitest";
import type {
  AgentDetail,
  AgentTemplate,
} from "@/shared/types/agent-registry-types";
import {
  buildAgentCreatePayload,
  buildAgentInvocationPreview,
  createAgentRegisterFormFromDetail,
  createAgentRegisterFormFromTemplate,
} from "./agent-registration";

const template: AgentTemplate = {
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
      type: "api_key_header",
      config: {
        headerName: "x-api-key",
        secret: "",
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
      max_retry: 2,
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
  },
};

const detail: AgentDetail = {
  agentId: "agt_001",
  templateId: "http_submit_poll_basic",
  name: "Skyvern Agent",
  description: "通过 Skyvern API 执行 Web 自动化任务",
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
};

describe("agent registration model", () => {
  it("uses template defaults to build a create payload", () => {
    const form = createAgentRegisterFormFromTemplate(template);
    form.name = "Skyvern Agent";
    form.description = "通过 Skyvern API 执行 Web 自动化任务";
    form.connection.baseUrl = "https://api.agent.example.com";
    form.auth.secret = "sk-demo";

    const result = buildAgentCreatePayload(form);

    expect(result.valid).toBe(true);
    expect(result.payload).toMatchObject({
      templateId: "http_submit_poll_basic",
      name: "Skyvern Agent",
      auth: {
        type: "api_key_header",
        config: {
          headerName: "x-api-key",
          secret: "sk-demo",
        },
      },
      customRequestBody: {
        engine: "skyvern-2.0",
        max_retry: 2,
      },
      terminalStatuses: ["completed", "failed", "timed_out"],
      successStatuses: ["completed"],
    });
  });

  it("clears credentials when prefilling a copied agent", () => {
    const form = createAgentRegisterFormFromDetail(detail);

    expect(form.name).toBe("Skyvern Agent 副本");
    expect(form.auth.type).toBe("api_key_header");
    expect(form.auth.headerName).toBe("x-api-key");
    expect(form.auth.secret).toBe("");
    expect(form.connection.baseUrl).toBe("https://api.agent.example.com");
  });

  it("builds a masked invocation preview from mappings and fixed fields", () => {
    const form = createAgentRegisterFormFromTemplate(template);
    form.connection.baseUrl = "https://api.agent.example.com";
    form.connection.invokePath = "/v1/run/tasks";
    form.auth.type = "api_key_header";
    form.auth.headerName = "x-api-key";
    form.auth.secret = "real-secret";

    const preview = buildAgentInvocationPreview(form);

    expect(preview.missingMessage).toBe("");
    expect(preview.requestBody).toMatchObject({
      prompt: "请完成平台下发的任务目标",
      url: "https://example.com",
      timeout_sec: 120,
      engine: "skyvern-2.0",
    });
    expect(preview.curl).toContain("x-api-key: <YOUR_API_KEY>");
    expect(preview.curl).not.toContain("real-secret");
    expect(preview.python).toContain('"x-api-key": "<YOUR_API_KEY>"');
  });
});
