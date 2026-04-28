import { describe, expect, it } from "vitest";
import {
  buildSubmitAgentOptions,
  filterAvailableSubmitAgents,
} from "./submit-agent-options";
import type {
  AgentListItem,
  AgentStatus,
} from "@/shared/types/agent-registry-types";

const createAgent = (
  agentId: string,
  status: AgentStatus,
  overrides: Partial<AgentListItem> = {},
): AgentListItem => ({
  agentId,
  name: agentId,
  description: "",
  invokeMode: "submit_poll",
  status,
  verifiedAt: null,
  lastVerificationPassed: null,
  canSubmitEvaluation: status === "active",
  canVerify: status === "draft" || status === "active" || status === "invalid",
  canArchive: status !== "archived" && status !== "verifying",
  canCopyCreate: true,
  createdAt: "2026-04-27T10:00:00.000Z",
  updatedAt: "2026-04-27T10:00:00.000Z",
  ...overrides,
});

describe("submit agent options", () => {
  it("keeps only active agents that can submit evaluations", () => {
    const activeAgent = createAgent("agt_active", "active");
    const blockedActiveAgent = createAgent("agt_blocked", "active", {
      canSubmitEvaluation: false,
    });

    expect(
      filterAvailableSubmitAgents([
        createAgent("agt_draft", "draft"),
        activeAgent,
        createAgent("agt_invalid", "invalid"),
        createAgent("agt_verifying", "verifying"),
        createAgent("agt_archived", "archived"),
        blockedActiveAgent,
      ]),
    ).toEqual([activeAgent]);
  });

  it("builds select options from available agents", () => {
    expect(
      buildSubmitAgentOptions([
        createAgent("agt_alpha", "active", {
          name: "Alpha Agent",
          invokeMode: "sync_response",
        }),
        createAgent("agt_draft", "draft", {
          name: "Draft Agent",
        }),
      ]),
    ).toEqual([
      {
        label: "Alpha Agent · 同步响应",
        value: "agt_alpha",
      },
    ]);
  });
});
