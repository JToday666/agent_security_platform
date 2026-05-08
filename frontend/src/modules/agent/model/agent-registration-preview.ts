import type {
  AgentInputMapping,
  AgentOutputMapping,
} from "@/shared/types/agent-registry-types";
import {
  buildAgentCustomRequestBody,
  getAgentAuthHeader,
  type AgentRegisterForm,
} from "./agent-registration-form";
import {
  normalizeAgentInputMapping,
  normalizeAgentOutputMapping,
  parseAgentOutputJsonPath,
} from "./agent-registration-validation";

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
  responseBody: Record<string, unknown>;
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

const STRUCTURED_OUTPUT_SCHEMA_SAMPLE = {
  type: "object",
  properties: {},
};

const RESPONSE_OUTPUT_SAMPLES: Record<keyof AgentOutputMapping, unknown> = {
  externalRunId: "run_123",
  status: "completed",
  finalAnswer: "最终答案",
  errorMessage: "错误信息",
};

const joinUrl = (baseUrl: string, path: string): string =>
  `${baseUrl.replace(/\/+$/, "")}/${path.replace(/^\/+/, "")}`;

const POLL_ONLY_OUTPUT_FIELDS: Array<keyof AgentOutputMapping> = [
  "externalRunId",
  "status",
];

const setJsonPathValue = (
  target: Record<string, unknown>,
  segments: string[],
  value: unknown,
) => {
  if (segments.length === 0) {
    return;
  }

  let cursor = target;
  segments.slice(0, -1).forEach((segment) => {
    const next = cursor[segment];
    if (!next || typeof next !== "object" || Array.isArray(next)) {
      cursor[segment] = {};
    }

    cursor = cursor[segment] as Record<string, unknown>;
  });

  cursor[segments[segments.length - 1]] = value;
};

const buildResponseMappingPreview = (
  form: AgentRegisterForm,
  baseUrl: string,
): AgentResponseMappingPreview => {
  const responsePaths: Partial<Record<keyof AgentOutputMapping, string>> = {};
  const responseBody: Record<string, unknown> = {};
  const outputMapping = normalizeAgentOutputMapping(form.platformOutputMapping);

  Object.entries(outputMapping).forEach(([field, path]) => {
    const outputField = field as keyof AgentOutputMapping;
    if (
      form.invokeMode === "sync_response" &&
      POLL_ONLY_OUTPUT_FIELDS.includes(outputField)
    ) {
      return;
    }

    const parsedPath = parseAgentOutputJsonPath(path);
    if (!parsedPath.valid) {
      return;
    }

    responsePaths[outputField] = parsedPath.normalized;
    setJsonPathValue(
      responseBody,
      parsedPath.segments,
      RESPONSE_OUTPUT_SAMPLES[outputField],
    );
  });

  const resultPath = form.connection.resultPathTemplate?.trim();

  return {
    invokeMode: form.invokeMode,
    resultEndpoint:
      form.invokeMode === "submit_poll" && baseUrl && resultPath
        ? joinUrl(baseUrl, resultPath)
        : null,
    responsePaths,
    responseBody,
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
  const inputMapping = normalizeAgentInputMapping(form.platformInputMapping);

  Object.entries(inputMapping).forEach(([platformField, target]) => {
    if (!target) {
      return;
    }

    requestBody[target] =
      PLATFORM_INPUT_SAMPLES[platformField as keyof AgentInputMapping];
  });

  const structuredOutputAlias = form.requestOptions.structuredOutput.supported
    ? form.requestOptions.structuredOutput.fieldAlias.trim()
    : "";
  if (structuredOutputAlias) {
    requestBody[structuredOutputAlias] = STRUCTURED_OUTPUT_SCHEMA_SAMPLE;
  }

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
