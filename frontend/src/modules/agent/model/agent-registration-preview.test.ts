import { describe, expect, it } from "vitest";
import {
  createCustomRequestField,
  createEmptyAgentRegisterForm,
} from "./agent-registration-form";
import { buildAgentInvocationPreview } from "./agent-registration-preview";

const createPreviewForm = () => {
  const form = createEmptyAgentRegisterForm();
  form.connection.baseUrl = "https://api.agent.example.com";
  form.connection.invokePath = "/v1/run/tasks";
  form.connection.resultPathTemplate = "/v1/run/tasks/{externalRunId}";
  form.auth.type = "none";
  form.platformInputMapping.task = "goal";
  form.platformInputMapping.entryUrl = "startUrl";
  form.platformInputMapping.timeoutSeconds = "";
  form.platformOutputMapping.externalRunId = "data.runId";
  form.platformOutputMapping.status = "data.status";
  form.platformOutputMapping.finalAnswer = "data.answer";
  form.platformOutputMapping.errorMessage = "data.error.message";
  form.customRequestFields = [
    {
      ...createCustomRequestField(),
      key: "source",
      valueType: "string",
      value: "platform",
    },
  ];
  return form;
};

describe("agent registration invocation preview", () => {
  it("builds the request body from fixed fields and input mapping samples", () => {
    const preview = buildAgentInvocationPreview(createPreviewForm());

    expect(preview.requestBody).toMatchObject({
      source: "platform",
      goal: "请完成平台下发的任务目标",
      startUrl: "https://example.com",
    });
    expect(preview.requestBody).not.toHaveProperty("timeoutSeconds");
  });

  it("includes output mapping paths in the response parsing preview", () => {
    const preview = buildAgentInvocationPreview(createPreviewForm());

    expect(preview.responseMapping).toMatchObject({
      invokeMode: "submit_poll",
      resultEndpoint: "https://api.agent.example.com/v1/run/tasks/{externalRunId}",
      responsePaths: {
        externalRunId: "data.runId",
        status: "data.status",
        finalAnswer: "data.answer",
        errorMessage: "data.error.message",
      },
      requiredPaths: ["externalRunId", "status"],
    });
  });

  it("does not require poll-only response paths for synchronous agents", () => {
    const form = createPreviewForm();
    form.invokeMode = "sync_response";

    const preview = buildAgentInvocationPreview(form);

    expect(preview.responseMapping.requiredPaths).toEqual([]);
    expect(preview.responseMapping.responsePaths).not.toHaveProperty("externalRunId");
    expect(preview.responseMapping.responsePaths).not.toHaveProperty("status");
    expect(preview.responseMapping.responsePaths).toMatchObject({
      finalAnswer: "data.answer",
      errorMessage: "data.error.message",
    });
  });
});
