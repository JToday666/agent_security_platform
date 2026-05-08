import { describe, expect, it } from "vitest";
import {
  buildAgentInvocationPreview,
  buildAgentCreatePayload,
  createAgentRegisterFormFromDetail,
  createAgentRegisterFormFromTemplate,
  createEmptyAgentRegisterForm,
  getNextAgentRegisterStep,
  getPreviousAgentRegisterStep,
  hasAgentRegisterConfigurationInput,
  validateAgentRegisterStep,
  type AgentRegisterForm,
  type AgentRegisterStepId,
} from "./agent-registration";
import type {
  AgentDetail,
  AgentTemplate,
} from "@/shared/types/agent-registry-types";

const createValidForm = (): AgentRegisterForm => {
  const form = createEmptyAgentRegisterForm();
  form.templateId = "custom";
  form.name = "Skyvern";
  form.connection.baseUrl = "https://api.skyvern.com";
  form.connection.invokePath = "/v1/run/tasks";
  form.connection.resultPathTemplate = "/v1/runs/{externalRunId}";
  form.auth.type = "none";
  form.platformInputMapping.task = "prompt";
  form.platformOutputMapping.externalRunId = "runId";
  form.platformOutputMapping.status = "status";
  form.terminalStatusesText = "completed, failed";
  form.successStatusesText = "completed";
  return form;
};

const createTemplate = (): AgentTemplate => ({
  templateId: "template_one",
  name: "Template One",
  description: "模板",
  recommended: false,
  sortOrder: 1,
  level: "basic",
  tags: [],
  defaultConfig: {
    invokeMode: "submit_poll",
    connection: {
      baseUrl: "https://agent.example.com",
      invokePath: "/tasks",
      resultPathTemplate: "/tasks/{externalRunId}",
      requestTimeoutSeconds: 45,
      pollIntervalSeconds: 3,
      pollTimeoutSeconds: 240,
    },
    auth: {
      type: "api_key_header",
      config: {
        headerName: "x-agent-key",
        secret: "",
      },
    },
    platformInputMapping: {
      task: "prompt",
      entryUrl: "url",
    },
    taskRenderMode: "goal_only",
    customRequestBody: {
      engine: "skyvern-2.0",
    },
    requestOptions: {
      structuredOutput: {
        supported: true,
        fieldAlias: "schema",
      },
    },
    platformOutputMapping: {
      externalRunId: "id",
      status: "state",
    },
    terminalStatuses: ["completed", "failed"],
    successStatuses: ["completed"],
  },
});

const createAgentDetail = (): AgentDetail => ({
  agentId: "agent_one",
  templateId: "template_one",
  name: "Existing Agent",
  description: "已有智能体",
  invokeMode: "submit_poll",
  status: "active",
  connection: {
    baseUrl: "https://agent.example.com",
    invokePath: "/tasks",
    resultPathTemplate: "/tasks/{externalRunId}",
    requestTimeoutSeconds: 45,
    pollIntervalSeconds: 3,
    pollTimeoutSeconds: 240,
  },
  auth: {
    type: "none",
  },
  platformInputMapping: {
    task: "prompt",
  },
  taskRenderMode: "goal_only",
  customRequestBody: {},
  requestOptions: {
    structuredOutput: {
      supported: false,
      fieldAlias: "",
    },
  },
  platformOutputMapping: {
    status: "state",
  },
  terminalStatuses: ["completed", "failed"],
  successStatuses: ["completed"],
  verifiedAt: "2026-05-01T00:00:00.000Z",
  lastVerification: null,
  actions: {
    canSubmitEvaluation: true,
    canVerify: true,
    canArchive: true,
    canCopyCreate: true,
  },
  createdAt: "2026-05-01T00:00:00.000Z",
  updatedAt: "2026-05-01T00:00:00.000Z",
});

describe("agent registration form defaults", () => {
  it("creates a no-template form without filled text, path, mapping, status, or structured alias values", () => {
    const form = createEmptyAgentRegisterForm();

    expect(form.connection.baseUrl).toBe("");
    expect(form.connection.invokePath).toBe("");
    expect(form.connection.resultPathTemplate).toBe("");
    expect(form.platformInputMapping).toEqual({
      task: "",
      entryUrl: "",
      timeoutSeconds: "",
      sampleId: "",
      evaluationId: "",
      maxSteps: "",
    });
    expect(form.platformOutputMapping).toEqual({
      externalRunId: "",
      status: "",
      finalAnswer: "",
      errorMessage: "",
    });
    expect(form.terminalStatusesText).toBe("");
    expect(form.successStatusesText).toBe("");
    expect(form.requestOptions.structuredOutput.fieldAlias).toBe("");
  });

  it("keeps safe non-text defaults for a no-template form", () => {
    const form = createEmptyAgentRegisterForm();

    expect(form.invokeMode).toBe("submit_poll");
    expect(form.auth.type).toBe("none");
    expect(form.connection.requestTimeoutSeconds).toBe(30);
    expect(form.connection.pollIntervalSeconds).toBe(2);
    expect(form.connection.pollTimeoutSeconds).toBe(300);
    expect(form.requestOptions.structuredOutput.supported).toBe(false);
  });

  it("fills the form exactly from template defaults without adding default mapping values", () => {
    const form = createAgentRegisterFormFromTemplate(createTemplate());

    expect(form.connection.invokePath).toBe("/tasks");
    expect(form.auth.headerName).toBe("x-agent-key");
    expect(form.platformInputMapping).toEqual({
      task: "prompt",
      entryUrl: "url",
      timeoutSeconds: "",
      sampleId: "",
      evaluationId: "",
      maxSteps: "",
    });
    expect(form.platformOutputMapping).toEqual({
      externalRunId: "id",
      status: "state",
      finalAnswer: "",
      errorMessage: "",
    });
    expect(form.requestOptions.structuredOutput.fieldAlias).toBe("schema");
  });

  it("copies an existing agent without adding mapping fields that the detail does not contain", () => {
    const form = createAgentRegisterFormFromDetail(createAgentDetail());

    expect(form.platformInputMapping).toEqual({
      task: "prompt",
      entryUrl: "",
      timeoutSeconds: "",
      sampleId: "",
      evaluationId: "",
      maxSteps: "",
    });
    expect(form.platformOutputMapping).toEqual({
      externalRunId: "",
      status: "state",
      finalAnswer: "",
      errorMessage: "",
    });
  });
});

describe("agent registration payload", () => {
  it("keeps minimal mappings valid and omits empty optional mapping fields", () => {
    const form = createValidForm();
    form.platformInputMapping = {
      task: " prompt ",
      entryUrl: "",
      timeoutSeconds: "  ",
      sampleId: "",
      evaluationId: "",
      maxSteps: "",
    };
    form.platformOutputMapping = {
      externalRunId: " runId ",
      status: " status ",
      finalAnswer: "",
      errorMessage: "  ",
    };

    const result = buildAgentCreatePayload(form);

    expect(result.valid).toBe(true);
    expect(result.payload?.platformInputMapping).toEqual({ task: "prompt" });
    expect(result.payload?.platformOutputMapping).toEqual({
      externalRunId: "runId",
      status: "status",
    });
  });

  it("accepts a general mapping configuration from a template", () => {
    const form = createAgentRegisterFormFromTemplate(createTemplate());
    form.name = "Template Agent";
    form.auth.type = "none";
    const result = buildAgentCreatePayload(form);

    expect(result.valid).toBe(true);
    expect(result.payload?.platformInputMapping).toEqual({
      task: "prompt",
      entryUrl: "url",
    });
    expect(result.payload?.platformOutputMapping).toEqual({
      externalRunId: "id",
      status: "state",
    });
  });

  it("accepts a complete mapping configuration with all optional fields", () => {
    const form = createValidForm();
    form.description = "用于真实环境提交任务";
    form.platformInputMapping = {
      task: "prompt",
      entryUrl: "url",
      timeoutSeconds: "timeoutSeconds",
      sampleId: "sampleId",
      evaluationId: "evaluationId",
      maxSteps: "maxSteps",
    };
    form.platformOutputMapping = {
      externalRunId: "data.runId",
      status: "data.status",
      finalAnswer: "data.answer",
      errorMessage: "data.error.message",
    };

    const result = buildAgentCreatePayload(form);

    expect(result.valid).toBe(true);
    expect(result.payload?.platformInputMapping).toEqual(
      form.platformInputMapping,
    );
    expect(result.payload?.platformOutputMapping).toEqual(
      form.platformOutputMapping,
    );
  });

  it("rejects input mapping values that are not top-level field names", () => {
    const form = createValidForm();
    form.platformInputMapping.task = "request.prompt";

    const result = buildAgentCreatePayload(form);

    expect(result.valid).toBe(false);
    expect(result.fieldErrors.taskMapping).toBe(
      "平台输入映射只能填写外部请求体的顶层字段名",
    );
  });

  it("rejects output mapping paths that the backend cannot read", () => {
    const invalidPaths = [
      "data..runId",
      ".runId",
      "$.data.runId",
      "items[0].id",
    ];

    invalidPaths.forEach((path) => {
      const form = createValidForm();
      form.platformOutputMapping.externalRunId = path;

      const result = buildAgentCreatePayload(form);

      expect(result.valid).toBe(false);
      expect(result.fieldErrors.outputMapping).toBe(
        "输出映射需填写响应字段路径，例如 runId 或 data.runId，暂不支持 $、数组下标或空路径段。",
      );
    });
  });

  it("accepts top-level and nested output mapping paths", () => {
    const form = createValidForm();
    form.platformOutputMapping = {
      externalRunId: "runId",
      status: "data.status",
      finalAnswer: "output.answer",
      errorMessage: "error.message",
    };

    const result = buildAgentCreatePayload(form);

    expect(result.valid).toBe(true);
    expect(result.payload?.platformOutputMapping).toEqual(
      form.platformOutputMapping,
    );
  });

  it("omits a structured output alias from the payload when structured output is disabled", () => {
    const form = createValidForm();
    form.requestOptions.structuredOutput.supported = false;
    form.requestOptions.structuredOutput.fieldAlias = "outputSchema";

    const result = buildAgentCreatePayload(form);

    expect(result.valid).toBe(true);
    expect(result.payload?.requestOptions.structuredOutput).toEqual({
      supported: false,
      fieldAlias: "",
    });
  });
});

describe("agent invocation preview", () => {
  it("adds the structured output alias to the request body as a placeholder schema", () => {
    const form = createValidForm();
    form.requestOptions.structuredOutput.supported = true;
    form.requestOptions.structuredOutput.fieldAlias = "outputSchema";

    const preview = buildAgentInvocationPreview(form);

    expect(preview.requestBody.outputSchema).toEqual({
      type: "object",
      properties: {},
    });
  });

  it("omits the structured output alias from the request body when it is disabled", () => {
    const form = createValidForm();
    form.requestOptions.structuredOutput.supported = false;
    form.requestOptions.structuredOutput.fieldAlias = "outputSchema";

    const preview = buildAgentInvocationPreview(form);

    expect(preview.requestBody).not.toHaveProperty("outputSchema");
  });

  it("builds a response parsing JSON sample from output mapping paths", () => {
    const form = createValidForm();
    form.platformOutputMapping = {
      externalRunId: "data.runId",
      status: "state",
      finalAnswer: "data.answer",
    };

    const preview = buildAgentInvocationPreview(form);

    expect(preview.responseMapping.responseBody).toEqual({
      data: {
        runId: "run_123",
        answer: "最终答案",
      },
      state: "completed",
    });
  });
});

describe("agent registration step validation", () => {
  it("uses the same top-level field rule when validating the input mapping step", () => {
    const form = createValidForm();
    form.platformInputMapping.task = "items[0]";

    const result = validateAgentRegisterStep("inputMapping", form);

    expect(result.valid).toBe(false);
    expect(result.fieldErrors.taskMapping).toBe(
      "平台输入映射只能填写外部请求体的顶层字段名",
    );
  });

  it("uses the same response path rule when validating the output mapping step", () => {
    const form = createValidForm();
    form.platformOutputMapping.status = "data..status";

    const result = validateAgentRegisterStep("outputMapping", form);

    expect(result.valid).toBe(false);
    expect(result.fieldErrors.outputMapping).toBe(
      "输出映射需填写响应字段路径，例如 runId 或 data.runId，暂不支持 $、数组下标或空路径段。",
    );
  });

  it("returns precise header auth errors for API key header mode", () => {
    const form = createValidForm();
    form.auth.type = "api_key_header";
    form.auth.headerName = "";
    form.auth.secret = "";

    const stepResult = validateAgentRegisterStep("connection", form);
    const payloadResult = buildAgentCreatePayload(form);

    expect(stepResult.valid).toBe(false);
    expect(stepResult.fieldErrors.authHeaderName).toBe("请填写 Header 名称");
    expect(stepResult.fieldErrors.authHeaderSecret).toBe("请填写 Header 密钥");
    expect(stepResult.fieldErrors.authSecret).toBeUndefined();
    expect(payloadResult.fieldErrors.authHeaderName).toBe("请填写 Header 名称");
    expect(payloadResult.fieldErrors.authHeaderSecret).toBe(
      "请填写 Header 密钥",
    );
  });

  it("returns precise header auth errors for custom header mode", () => {
    const form = createValidForm();
    form.auth.type = "custom_header";
    form.auth.headerName = "X-Agent-Token";
    form.auth.secret = "";

    const result = validateAgentRegisterStep("connection", form);

    expect(result.valid).toBe(false);
    expect(result.fieldErrors.authHeaderName).toBeUndefined();
    expect(result.fieldErrors.authHeaderSecret).toBe("请填写 Header 密钥");
    expect(result.fieldErrors.authSecret).toBeUndefined();
  });
});

describe("agent registration template change detection", () => {
  it("treats mappings, paths, statuses, and structured output aliases as configuration input", () => {
    const form = createEmptyAgentRegisterForm();
    expect(hasAgentRegisterConfigurationInput(form)).toBe(false);

    form.connection.invokePath = "/runs";
    expect(hasAgentRegisterConfigurationInput(form)).toBe(true);

    const mappingForm = createEmptyAgentRegisterForm();
    mappingForm.platformOutputMapping.status = "status";
    expect(hasAgentRegisterConfigurationInput(mappingForm)).toBe(true);

    const structuredForm = createEmptyAgentRegisterForm();
    structuredForm.requestOptions.structuredOutput.supported = true;
    structuredForm.requestOptions.structuredOutput.fieldAlias = "schema";
    expect(hasAgentRegisterConfigurationInput(structuredForm)).toBe(true);
  });
});

describe("agent registration step navigation", () => {
  it("returns null when the current step is not present in the step list", () => {
    const steps = [
      { id: "template" as const, title: "选择模板", description: "" },
      { id: "basic" as const, title: "基本信息", description: "" },
    ];
    const missingStep = "connection" as AgentRegisterStepId;

    expect(getNextAgentRegisterStep(missingStep, steps)).toBeNull();
    expect(getPreviousAgentRegisterStep(missingStep, steps)).toBeNull();
  });
});
