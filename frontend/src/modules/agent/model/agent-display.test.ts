import { describe, expect, it } from "vitest";
import { getAgentSubmitDisabledReason } from "@/modules/agent/model/agent-display";
import type {
  AgentListItem,
  AgentStatus,
} from "@/shared/types/agent-registry-types";

const t = (key: string) => key;

const createAgent = (
  status: AgentStatus,
  canSubmitEvaluation = status === "active",
): AgentListItem => ({
  agentId: `agent_${status}`,
  name: "Agent",
  description: "",
  invokeMode: "submit_poll",
  status,
  verifiedAt: null,
  lastVerificationPassed: null,
  canSubmitEvaluation,
  canVerify: true,
  canArchive: true,
  canCopyCreate: true,
  createdAt: "2026-05-01T00:00:00.000Z",
  updatedAt: "2026-05-01T00:00:00.000Z",
});

describe("agent display helpers", () => {
  it("does not report a disabled reason for active submittable agents", () => {
    expect(getAgentSubmitDisabledReason(createAgent("active", true), t)).toBe(
      "",
    );
  });

  it("reports a disabled reason for active agents that cannot submit", () => {
    expect(getAgentSubmitDisabledReason(createAgent("active", false), t)).toBe(
      "agent.display.disabledReasons.unavailable",
    );
  });

  it.each([
    ["draft", "agent.display.disabledReasons.draft"],
    ["verifying", "agent.display.disabledReasons.verifying"],
    ["invalid", "agent.display.disabledReasons.invalid"],
    ["archived", "agent.display.disabledReasons.archived"],
  ] as const)("reports disabled reason for %s agents", (status, reasonKey) => {
    expect(getAgentSubmitDisabledReason(createAgent(status), t)).toBe(
      reasonKey,
    );
  });
});
