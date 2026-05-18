import { describe, expect, it } from "vitest";
import type { AgentDetail } from "@/shared/types/agent-registry-types";
import { AGENT_NO_TEMPLATE_ID } from "./agent-registration-constants";
import { createAgentRegisterFormFromDetail } from "./agent-registration-form";

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
});
