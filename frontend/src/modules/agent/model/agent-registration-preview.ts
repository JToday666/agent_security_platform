import type { AgentInputMapping } from "@/shared/types/agent-registry-types";
import {
  buildAgentCustomRequestBody,
  getAgentAuthHeader,
  type AgentRegisterForm,
} from "./agent-registration-form";

export interface AgentInvocationPreview {
  missingMessage: string;
  requestBody: Record<string, unknown>;
  curl: string;
  python: string;
}

const PLATFORM_INPUT_SAMPLES: Record<keyof AgentInputMapping, unknown> = {
  task: "请完成平台下发的任务目标",
  entryUrl: "https://example.com",
  timeoutSeconds: 120,
  sampleId: "sample_001",
  evaluationId: "eval_001",
  maxSteps: 30,
};

const joinUrl = (baseUrl: string, path: string): string =>
  `${baseUrl.replace(/\/+$/, "")}/${path.replace(/^\/+/, "")}`;

export const buildAgentInvocationPreview = (
  form: AgentRegisterForm,
): AgentInvocationPreview => {
  const baseUrl = form.connection.baseUrl.trim();
  const invokePath = form.connection.invokePath.trim();
  const customBody = buildAgentCustomRequestBody(form.customRequestFields).body;
  const requestBody: Record<string, unknown> = { ...customBody };

  Object.entries(form.platformInputMapping).forEach(
    ([platformField, target]) => {
      const targetField = target?.trim();
      if (!targetField) {
        return;
      }

      requestBody[targetField] =
        PLATFORM_INPUT_SAMPLES[platformField as keyof AgentInputMapping];
    },
  );

  if (!baseUrl || !invokePath) {
    return {
      missingMessage: "请填写 baseUrl 和 invokePath 后查看调用预览。",
      requestBody,
      curl: "",
      python: "",
    };
  }

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  const authHeader = getAgentAuthHeader(form);
  if (authHeader) {
    headers[authHeader.name] = authHeader.value;
  }

  const url = joinUrl(baseUrl, invokePath);
  const payloadJson = JSON.stringify(requestBody, null, 2);
  const curlHeaders = Object.entries(headers)
    .map(([name, value]) => `  --header '${name}: ${value}' \\`)
    .join("\n");
  const curl = [
    "curl --request POST \\",
    `  --url '${url}' \\`,
    curlHeaders,
    `  --data '${payloadJson}'`,
  ].join("\n");
  const python = [
    "import requests",
    "",
    `url = "${url}"`,
    "",
    `headers = ${JSON.stringify(headers, null, 4)}`,
    "",
    `payload = ${JSON.stringify(requestBody, null, 4)}`,
    "",
    `response = requests.post(url, headers=headers, json=payload, timeout=${form.connection.requestTimeoutSeconds})`,
    "print(response.status_code)",
    "print(response.json())",
  ].join("\n");

  return {
    missingMessage: "",
    requestBody,
    curl,
    python,
  };
};
