import { describe, expect, it } from "vitest";
import {
  buildEvaluationCreatePayload,
  validateSubmitPayload,
} from "./parameter-validator";
import type {
  SubmitAgentPayload,
  SubmitMetaResponse,
} from "@/shared/types/agent-types";

const meta: SubmitMetaResponse = {
  supportedMethods: ["api", "docker"],
  difficulty: {
    min: 0,
    max: 1,
    step: 0.1,
    default: 0.5,
  },
  timeoutMinutes: {
    min: 15,
    max: 30,
    step: 1,
    default: 15,
  },
  maxSteps: {
    min: 1,
    max: 100,
    step: 1,
    default: 30,
  },
  publicToLeaderboard: {
    default: true,
  },
};

const payload: SubmitAgentPayload = {
  submitMethod: "api",
  agentId: "agt_active",
  docker: null,
  parameters: {
    difficulty: 0.5,
    timeoutMinutes: 20,
    maxSteps: 30,
  },
  publicToLeaderboard: false,
  selectedDatasetIds: ["A1_identity_leakage"],
  requestId: "submit_20260427_demo001",
};

describe("submit payload", () => {
  it("creates the new evaluations payload for API agent submissions", () => {
    expect(buildEvaluationCreatePayload(payload)).toEqual({
      requestId: "submit_20260427_demo001",
      submitMethod: "api",
      agentId: "agt_active",
      datasetIds: ["A1_identity_leakage"],
      parameters: {
        difficulty: 0.5,
        timeoutMinutes: 20,
        maxSteps: 30,
      },
      publicToLeaderboard: false,
    });
  });

  it("requires an active registered agent for API submissions", () => {
    const result = validateSubmitPayload(
      { ...payload, agentId: "agt_invalid" },
      meta,
      ["A1_identity_leakage"],
      ["agt_active"],
    );

    expect(result.valid).toBe(false);
    expect(result.fieldErrors.agentId).toBe("请选择可评测智能体");
  });

  it("keeps Docker submissions disabled during the upgrade", () => {
    const result = validateSubmitPayload(
      {
        ...payload,
        submitMethod: "docker",
        agentId: null,
        docker: {
          imageUri: "registry.example.com/web-agent:latest",
          command: "python run.py",
          env: {
            AGENT_MODE: "eval",
          },
        },
      },
      meta,
      ["A1_identity_leakage"],
      ["agt_active"],
    );

    expect(result.valid).toBe(false);
    expect(result.errors).toContain("Docker 提交功能正在升级中。");
  });
});
