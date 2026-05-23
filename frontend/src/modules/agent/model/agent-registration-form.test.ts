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
  createAgentRegisterFormFromDetail,
  createAgentRegisterFormFromTemplate,
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
  connection: {
    baseUrl: "https://agent.example.com",
    invokePath: "/api/runs",
    resultPathTemplate: "/api/runs/{externalRunId}",
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
    connection: {
      baseUrl: "https://api.browser-use.com",
      invokePath: "/api/v3/sessions",
      resultPathTemplate: "/api/v3/sessions/{externalRunId}",
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
});

describe("createAgentRegisterFormFromTemplate", () => {
  it("prefills Browser Use templates without dropping success or taskRenderMode", () => {
    const form = createAgentRegisterFormFromTemplate(createBrowserUseV3Template());

    expect(form.taskRenderMode).toBe("goal_with_entry_url");
    expect(form.platformOutputMapping.success).toBe("isTaskSuccessful");
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
