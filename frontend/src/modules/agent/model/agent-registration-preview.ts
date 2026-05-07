import type {
  AgentInputMapping,
  AgentOutputMapping,
} from "@/shared/types/agent-registry-types";
import {
  buildAgentCustomRequestBody,
  getAgentAuthHeader,
  type AgentRegisterForm,
} from "./agent-registration-form";

export interface AgentInvocationPreview {
  missingMessage: string;
  requestBody: Record<string, unknown>;
  responseMapping: AgentResponseMappingPreview;
  curl: string;
  python: string;
}

export interface AgentResponseMappingPreview {
  invokeMode: AgentRegisterForm["invokeMode"];
  resultEndpoint: string | null;
  responsePaths: Partial<Record<keyof AgentOutputMapping, string>>;
  requiredPaths: Array<keyof AgentOutputMapping>;
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

const POLL_ONLY_OUTPUT_FIELDS: Array<keyof AgentOutputMapping> = [
  "externalRunId",
  "status",
];

const buildResponseMappingPreview = (
  form: AgentRegisterForm,
  baseUrl: string,
): AgentResponseMappingPreview => {
  const responsePaths: Partial<Record<keyof AgentOutputMapping, string>> = {};

  Object.entries(form.platformOutputMapping).forEach(([field, path]) => {
    const outputField = field as keyof AgentOutputMapping;
    const responsePath = path?.trim();
    if (
      !responsePath ||
      (form.invokeMode === "sync_response" &&
        POLL_ONLY_OUTPUT_FIELDS.includes(outputField))
    ) {
      return;
    }

    responsePaths[outputField] = responsePath;
  });

  const resultPath = form.connection.resultPathTemplate?.trim();

  return {
    invokeMode: form.invokeMode,
    resultEndpoint:
      form.invokeMode === "submit_poll" && baseUrl && resultPath
        ? joinUrl(baseUrl, resultPath)
        : null,
    responsePaths,
    requiredPaths:
      form.invokeMode === "submit_poll" ? [...POLL_ONLY_OUTPUT_FIELDS] : [],
  };
};

export const buildAgentInvocationPreview = (
  form: AgentRegisterForm,
): AgentInvocationPreview => {
  const baseUrl = form.connection.baseUrl.trim();
  const invokePath = form.connection.invokePath.trim();
  const customBody = buildAgentCustomRequestBody(form.customRequestFields).body;
  const requestBody: Record<string, unknown> = { ...customBody };
  const responseMapping = buildResponseMappingPreview(form, baseUrl);

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
      responseMapping,
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
    responseMapping,
    curl,
    python,
  };
};
