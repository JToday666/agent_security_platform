import { describe, expect, it } from "vitest";
import type {
  AgentDetail,
  AgentTemplate,
} from "@/shared/types/agent-registry-types";
import { buildAgentOutputMappingItems } from "@/modules/agent/lib/agent-detail-view";
import { AGENT_NO_TEMPLATE_ID } from "./agent-registration-constants";
import { buildAgentCreatePayload } from "./agent-registration-payload";
import { buildAgentInvocationPreview } from "./agent-registration-preview";
import {
  clearAgentCancelRequestBody,
  createAgentRegisterFormFromDetail,
  createAgentRegisterFormFromTemplate,
  parseAgentMaxConcurrencyInput,
} from "./agent-registration-form";

const t = (key: string, params?: Record<string, unknown>) =>
  key === "agent.register.copyName" ? `Copy of ${params?.name}` : key;

const createDetail = (
  templateId?: AgentDetail["templateId"],
): AgentDetail => ({
  agentId: "agt_demo",
  templateId,
  name: "Demo Agent",
  description: "Copied Agent",
  invokeMode: "submit_poll",
  maxConcurrency: 6,
  connection: {
    baseUrl: "https://agent.example.com",
    invokePath: "/api/runs",
    resultPathTemplate: "/api/runs/{externalRunId}",
    cancelPathTemplate: "/api/runs/{externalRunId}/cancel",
    cancelMethod: "POST",
    cancelRequestBody: null,
    requestTimeoutSeconds: 30,
    pollIntervalSeconds: 2,
    pollTimeoutSeconds: 300,
  },
  auth: {
    type: "bearer",
    hasCredential: true,
    publicConfig: {},
  },
  platformInputMapping: {
    task: "task",
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
    status: "status",
    finalAnswer: "answer",
    success: "isTaskSuccessful",
  },
  status: "active",
  terminalStatuses: ["completed", "failed"],
  successStatuses: ["completed"],
  actions: {
    canSubmitEvaluation: true,
    canVerify: true,
    canArchive: true,
    canCopyCreate: true,
  },
  createdAt: "2026-05-18T00:00:00Z",
  updatedAt: "2026-05-18T00:00:00Z",
});

const createBrowserUseV3Template = (): AgentTemplate => ({
  templateId: "browser_use_cloud_v3_sessions",
  name: "Browser Use v3 Sessions",
  description: "Browser Use v3 session template",
  recommended: false,
  sortOrder: 40,
  level: "cloud",
  tags: ["browser-use", "v3"],
  defaultConfig: {
    invokeMode: "submit_poll",
    maxConcurrency: 7,
    connection: {
      baseUrl: "https://api.browser-use.com",
      invokePath: "/api/v3/sessions",
      resultPathTemplate: "/api/v3/sessions/{externalRunId}",
      cancelPathTemplate: "/api/v3/sessions/{externalRunId}",
      cancelMethod: "DELETE",
      cancelRequestBody: null,
      requestTimeoutSeconds: 30,
      pollIntervalSeconds: 2,
      pollTimeoutSeconds: 300,
    },
    auth: {
      type: "none",
      config: {},
    },
    platformInputMapping: {
      task: "task",
    },
    taskRenderMode: "goal_with_entry_url",
    customRequestBody: {},
    requestOptions: {
      structuredOutput: {
        supported: true,
        fieldAlias: "outputSchema",
      },
    },
    platformOutputMapping: {
      externalRunId: "id",
      status: "status",
      success: "isTaskSuccessful",
      finalAnswer: "output",
      errorMessage: "lastStepSummary",
    },
    terminalStatuses: ["stopped", "timed_out", "error"],
    successStatuses: ["stopped"],
  },
});

describe("createAgentRegisterFormFromDetail", () => {
  it("maps missing detail template ids to the custom template sentinel", () => {
    expect(createAgentRegisterFormFromDetail(createDetail(null), t).templateId).toBe(
      AGENT_NO_TEMPLATE_ID,
    );
    expect(
      createAgentRegisterFormFromDetail(createDetail(undefined), t).templateId,
    ).toBe(AGENT_NO_TEMPLATE_ID);
    expect(createAgentRegisterFormFromDetail(createDetail("   "), t).templateId).toBe(
      AGENT_NO_TEMPLATE_ID,
    );
  });

  it("preserves concrete detail template ids", () => {
    expect(
      createAgentRegisterFormFromDetail(
        createDetail("http_submit_poll_basic"),
        t,
      ).templateId,
    ).toBe("http_submit_poll_basic");
  });

  it("preserves detail success output mapping and task render mode", () => {
    const detail = {
      ...createDetail("browser_use_cloud_v3_sessions"),
      taskRenderMode: "goal_with_entry_url" as const,
    };
    const form = createAgentRegisterFormFromDetail(detail, t);

    expect(form.taskRenderMode).toBe("goal_with_entry_url");
    expect(form.platformOutputMapping.success).toBe("isTaskSuccessful");
  });

  it("preserves detail max concurrency and cancel configuration", () => {
    const form = createAgentRegisterFormFromDetail(
      createDetail("http_submit_poll_basic"),
      t,
    );

    expect(form.maxConcurrency).toBe(6);
    expect(form.connection.cancelMethod).toBe("POST");
    expect(form.connection.cancelPathTemplate).toBe(
      "/api/runs/{externalRunId}/cancel",
    );
    expect(form.connection.cancelRequestBody).toBeNull();
  });
});

describe("createAgentRegisterFormFromTemplate", () => {
  it("prefills Browser Use templates without dropping success or taskRenderMode", () => {
    const form = createAgentRegisterFormFromTemplate(createBrowserUseV3Template());

    expect(form.taskRenderMode).toBe("goal_with_entry_url");
    expect(form.platformOutputMapping.success).toBe("isTaskSuccessful");
  });

  it("prefills max concurrency and cancel configuration from templates", () => {
    const form = createAgentRegisterFormFromTemplate(createBrowserUseV3Template());

    expect(form.maxConcurrency).toBe(7);
    expect(form.connection.cancelMethod).toBe("DELETE");
    expect(form.connection.cancelPathTemplate).toBe(
      "/api/v3/sessions/{externalRunId}",
    );
    expect(form.connection.cancelRequestBody).toBeNull();
  });
});

describe("buildAgentCreatePayload", () => {
  it("preserves success output mapping and taskRenderMode in payload", () => {
    const form = createAgentRegisterFormFromTemplate(createBrowserUseV3Template());
    form.name = "Browser Use v3";
    form.description = "Runs Browser Use v3 sessions";

    const result = buildAgentCreatePayload(form, t);

    expect(result.valid).toBe(true);
    expect(result.payload?.taskRenderMode).toBe("goal_with_entry_url");
    expect(result.payload?.platformOutputMapping.success).toBe(
      "isTaskSuccessful",
    );
  });

  it("includes max concurrency and cancel configuration in payload", () => {
    const form = createAgentRegisterFormFromTemplate(createBrowserUseV3Template());
    form.name = "Browser Use v3";
    form.description = "Runs Browser Use v3 sessions";

    const result = buildAgentCreatePayload(form, t);

    expect(result.valid).toBe(true);
    expect(result.payload?.maxConcurrency).toBe(7);
    expect(result.payload?.connection.cancelMethod).toBe("DELETE");
    expect(result.payload?.connection.cancelPathTemplate).toBe(
      "/api/v3/sessions/{externalRunId}",
    );
  });

  it("requires max concurrency before building payload", () => {
    const form = createAgentRegisterFormFromTemplate(createBrowserUseV3Template());
    form.name = "Browser Use v3";
    form.maxConcurrency = null;

    const result = buildAgentCreatePayload(form, t);

    expect(result.valid).toBe(false);
    expect(result.fieldErrors.maxConcurrency).toBe(
      "agent.validation.maxConcurrencyRequired",
    );
  });

  it("rejects max concurrency outside the supported range", () => {
    const form = createAgentRegisterFormFromTemplate(createBrowserUseV3Template());
    form.name = "Browser Use v3";
    form.maxConcurrency = 101;

    const result = buildAgentCreatePayload(form, t);

    expect(result.valid).toBe(false);
    expect(result.fieldErrors.maxConcurrency).toBe(
      "agent.validation.maxConcurrencyRange",
    );
  });

  it("omits cancel path and body when cancel path is blank", () => {
    const form = createAgentRegisterFormFromTemplate(createBrowserUseV3Template());
    form.name = "Browser Use v3";
    form.connection.cancelPathTemplate = "   ";
    form.connection.cancelRequestBody = { action: "stop" };

    const result = buildAgentCreatePayload(form, t);

    expect(result.valid).toBe(true);
    expect(result.payload?.connection.cancelMethod).toBeUndefined();
    expect(result.payload?.connection.cancelPathTemplate).toBeUndefined();
    expect(result.payload?.connection.cancelRequestBody).toBeUndefined();
  });

  it("rejects cancel paths without the external run id placeholder", () => {
    const form = createAgentRegisterFormFromTemplate(createBrowserUseV3Template());
    form.name = "Browser Use v3";
    form.connection.cancelPathTemplate = "/api/v3/sessions/current";

    const result = buildAgentCreatePayload(form, t);

    expect(result.valid).toBe(false);
    expect(result.fieldErrors.cancelPathTemplate).toBe(
      "agent.validation.cancelPathTemplateRequired",
    );
  });
});

describe("parseAgentMaxConcurrencyInput", () => {
  it("preserves entered numbers for validation instead of clamping them", () => {
    expect(parseAgentMaxConcurrencyInput("0")).toBe(0);
    expect(parseAgentMaxConcurrencyInput("101")).toBe(101);
    expect(parseAgentMaxConcurrencyInput("1.5")).toBe(1.5);
    expect(parseAgentMaxConcurrencyInput("")).toBeNull();
    expect(Number.isNaN(parseAgentMaxConcurrencyInput("abc"))).toBe(true);
  });
});

describe("clearAgentCancelRequestBody", () => {
  it("clears hidden cancel request body after the visible cancel endpoint changes", () => {
    const form = createAgentRegisterFormFromTemplate(createBrowserUseV3Template());
    form.connection.cancelRequestBody = { action: "stop_task_and_session" };

    clearAgentCancelRequestBody(form);

    expect(form.connection.cancelRequestBody).toBeNull();
  });
});

describe("buildAgentInvocationPreview", () => {
  it("renders Browser Use v3 goal_with_entry_url task text", () => {
    const form = createAgentRegisterFormFromTemplate(createBrowserUseV3Template());
    const preview = buildAgentInvocationPreview(form, t);

    expect(preview.requestBody.task).toContain("Start URL: https://example.com");
    expect(preview.responseMapping.responseBody).toMatchObject({
      isTaskSuccessful: true,
    });
  });
});

describe("buildAgentOutputMappingItems", () => {
  it("includes the success mapping in detail output display", () => {
    const items = buildAgentOutputMappingItems(
      {
        status: "status",
        success: "isTaskSuccessful",
      },
      t,
    );

    expect(items.some((item) => item.target === "success")).toBe(true);
  });
});
