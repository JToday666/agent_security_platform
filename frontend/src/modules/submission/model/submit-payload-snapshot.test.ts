import { describe, expect, it } from "vitest";
import {
  buildSubmitPayloadFromSnapshot,
  buildSubmitPayloadSnapshot,
  type SubmitPayloadSnapshot,
} from "@/modules/submission/model/submit-payload-snapshot";
import type {
  SubmitFormState,
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
    min: 1,
    max: 60,
    step: 1,
    default: 10,
  },
  maxSteps: {
    min: 1,
    max: 20,
    step: 1,
    default: 5,
  },
  leaderboardDisplayMode: {
    default: "public",
    options: ["public", "anonymous"],
  },
};

const createForm = (
  submitMethod: SubmitFormState["submitMethod"],
): SubmitFormState => ({
  submitMethod,
  agentId: " agent-1 ",
  docker: {
    imageUri: " registry.example.com/agent:latest ",
    command: " npm start ",
  },
  parameters: {
    difficulty: 0.52,
    timeoutMinutes: 12.4,
    maxSteps: 6.2,
  },
  leaderboardDisplayMode: "anonymous",
  selectedDatasetIds: ["dataset-b", "dataset-a", "dataset-b"],
});

describe("submit payload snapshot", () => {
  it("does not keep the legacy docker environment text field", () => {
    const snapshot = buildSubmitPayloadSnapshot(createForm("api"), meta);

    expect(snapshot).toEqual({
      submitMethod: "api",
      agentId: "agent-1",
      parameters: {
        difficulty: 0.5,
        timeoutMinutes: 12,
        maxSteps: 6,
      },
      leaderboardDisplayMode: "anonymous",
      datasetIds: ["dataset-a", "dataset-b"],
    });
  });

  it("builds docker payload with an empty env object while docker is unavailable", () => {
    const form = createForm("docker");
    const snapshot: SubmitPayloadSnapshot = {
      submitMethod: "docker",
      agentId: "",
      parameters: form.parameters,
      leaderboardDisplayMode: form.leaderboardDisplayMode,
      datasetIds: form.selectedDatasetIds,
    };

    expect(
      buildSubmitPayloadFromSnapshot(snapshot, form, "request-12345678"),
    ).toMatchObject({
      submitMethod: "docker",
      agentId: null,
      docker: {
        imageUri: "registry.example.com/agent:latest",
        command: "npm start",
        env: {},
      },
    });
  });
});
