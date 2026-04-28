import type {
  AgentAuthType,
  AgentConnectionConfig,
  AgentCreatePayload,
  AgentDetail,
  AgentInputMapping,
  AgentInvokeMode,
  AgentOutputMapping,
  AgentRequestOptions,
  AgentTemplate,
} from "@/shared/types/agent-registry-types";
import { isValidHttpUrl } from "@/modules/submission/model/parameter-validator";

export type AgentCustomFieldType = "string" | "number" | "boolean" | "json";

export interface AgentCustomRequestField {
  id: string;
  key: string;
  valueType: AgentCustomFieldType;
  value: string;
}

export interface AgentRegisterForm {
  templateId: string;
  name: string;
  description: string;
  invokeMode: AgentInvokeMode;
  connection: AgentConnectionConfig;
  auth: {
    type: AgentAuthType;
    token: string;
    headerName: string;
    secret: string;
  };
  platformInputMapping: AgentInputMapping;
  taskRenderMode: "goal_only";
  customRequestFields: AgentCustomRequestField[];
  requestOptions: AgentRequestOptions;
  platformOutputMapping: AgentOutputMapping;
  terminalStatusesText: string;
  successStatusesText: string;
}

export interface AgentRegisterFieldErrors {
  templateId?: string;
  name?: string;
  baseUrl?: string;
  invokePath?: string;
  resultPathTemplate?: string;
  taskMapping?: string;
  customRequestBody?: string;
  outputMapping?: string;
  terminalStatuses?: string;
  successStatuses?: string;
  authSecret?: string;
}

export interface AgentCreatePayloadResult {
  valid: boolean;
  errors: string[];
  fieldErrors: AgentRegisterFieldErrors;
  payload: AgentCreatePayload | null;
}

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

const DEFAULT_CONNECTION: AgentConnectionConfig = {
  baseUrl: "",
  invokePath: "/api/runs",
  resultPathTemplate: "/api/runs/{externalRunId}",
  requestTimeoutSeconds: 30,
  pollIntervalSeconds: 2,
  pollTimeoutSeconds: 300,
};

const DEFAULT_INPUT_MAPPING: AgentInputMapping = {
  task: "task",
  entryUrl: "entryUrl",
  timeoutSeconds: "timeoutSeconds",
  sampleId: "sampleId",
  evaluationId: "evaluationId",
  maxSteps: "maxSteps",
};

const DEFAULT_OUTPUT_MAPPING: AgentOutputMapping = {
  externalRunId: "data.runId",
  status: "data.status",
  finalAnswer: "data.answer",
  errorMessage: "data.error.message",
  stepCount: "data.metrics.stepCount",
  artifacts: "data.artifacts",
};

let customFieldIdSeed = 0;

const nextCustomFieldId = (): string => {
  customFieldIdSeed += 1;
  return `field_${customFieldIdSeed}`;
};

const toText = (value: unknown): string =>
  typeof value === "string" ? value.trim() : "";

const cloneJson = <T>(value: T): T => JSON.parse(JSON.stringify(value)) as T;

const normalizeConnection = (
  connection?: Partial<AgentConnectionConfig>,
): AgentConnectionConfig => ({
  ...DEFAULT_CONNECTION,
  ...connection,
  requestTimeoutSeconds: Number(connection?.requestTimeoutSeconds ?? 30),
  pollIntervalSeconds: Number(connection?.pollIntervalSeconds ?? 2),
  pollTimeoutSeconds: Number(connection?.pollTimeoutSeconds ?? 300),
});

const normalizeRequestOptions = (
  requestOptions?: Partial<AgentRequestOptions>,
): AgentRequestOptions => ({
  structuredOutput: {
    supported: Boolean(requestOptions?.structuredOutput?.supported),
    fieldAlias: toText(requestOptions?.structuredOutput?.fieldAlias),
  },
});

const detectFieldType = (value: unknown): AgentCustomFieldType => {
  if (typeof value === "number") {
    return "number";
  }

  if (typeof value === "boolean") {
    return "boolean";
  }

  if (value && typeof value === "object") {
    return "json";
  }

  return "string";
};

const stringifyCustomValue = (value: unknown): string => {
  if (typeof value === "string") {
    return value;
  }

  if (value && typeof value === "object") {
    return JSON.stringify(value, null, 2);
  }

  return String(value ?? "");
};

const customBodyToFields = (
  customRequestBody: Record<string, unknown> = {},
): AgentCustomRequestField[] =>
  Object.entries(customRequestBody).map(([key, value]) => ({
    id: nextCustomFieldId(),
    key,
    valueType: detectFieldType(value),
    value: stringifyCustomValue(value),
  }));

const parseStatusText = (value: string): string[] =>
  value
    .split(/[\n,]/)
    .map((item) => item.trim())
    .filter((item) => item.length > 0);

const parseCustomFieldValue = (
  field: AgentCustomRequestField,
): { ok: true; value: unknown } | { ok: false; message: string } => {
  const value = field.value.trim();

  if (field.valueType === "string") {
    return { ok: true, value: field.value };
  }

  if (field.valueType === "number") {
    const parsed = Number(value);
    return Number.isFinite(parsed)
      ? { ok: true, value: parsed }
      : { ok: false, message: `${field.key || "自定义字段"} 必须是数字。` };
  }

  if (field.valueType === "boolean") {
    if (value === "true" || value === "false") {
      return { ok: true, value: value === "true" };
    }

    return {
      ok: false,
      message: `${field.key || "自定义字段"} 必须填写 true 或 false。`,
    };
  }

  try {
    return { ok: true, value: JSON.parse(value) };
  } catch {
    return {
      ok: false,
      message: `${field.key || "自定义字段"} 不是有效 JSON。`,
    };
  }
};

const buildCustomRequestBody = (
  fields: AgentCustomRequestField[],
): { body: Record<string, unknown>; errors: string[] } => {
  const body: Record<string, unknown> = {};
  const errors: string[] = [];

  fields.forEach((field) => {
    const key = field.key.trim();
    if (!key && !field.value.trim()) {
      return;
    }

    if (!key) {
      errors.push("自定义固定字段必须填写字段名。");
      return;
    }

    if (Object.prototype.hasOwnProperty.call(body, key)) {
      errors.push(`自定义固定字段 ${key} 重复。`);
      return;
    }

    const parsed = parseCustomFieldValue(field);
    if (!parsed.ok) {
      errors.push(parsed.message);
      return;
    }

    body[key] = parsed.value;
  });

  return { body, errors };
};

const buildAuthConfig = (
  form: AgentRegisterForm,
): { type: AgentAuthType; config: Record<string, string> } => {
  if (form.auth.type === "none") {
    return { type: "none", config: {} };
  }

  if (form.auth.type === "bearer") {
    return {
      type: "bearer",
      config: {
        token: form.auth.token.trim(),
      },
    };
  }

  return {
    type: form.auth.type,
    config: {
      headerName: form.auth.headerName.trim(),
      secret: form.auth.secret.trim(),
    },
  };
};

const getAuthHeader = (
  form: AgentRegisterForm,
): { name: string; value: string } | null => {
  if (form.auth.type === "bearer") {
    return { name: "Authorization", value: "Bearer <YOUR_TOKEN>" };
  }

  if (form.auth.type === "api_key_header") {
    return {
      name: form.auth.headerName.trim() || "x-api-key",
      value: "<YOUR_API_KEY>",
    };
  }

  if (form.auth.type === "custom_header") {
    return {
      name: form.auth.headerName.trim() || "X-Agent-Token",
      value: "<YOUR_SECRET>",
    };
  }

  return null;
};

const joinUrl = (baseUrl: string, path: string): string =>
  `${baseUrl.replace(/\/+$/, "")}/${path.replace(/^\/+/, "")}`;

export const createAgentRegisterFormFromTemplate = (
  template: AgentTemplate,
): AgentRegisterForm => {
  const defaultConfig = template.defaultConfig;

  return {
    templateId: template.templateId,
    name: "",
    description: "",
    invokeMode: defaultConfig.invokeMode,
    connection: normalizeConnection(defaultConfig.connection),
    auth: {
      type: defaultConfig.auth.type,
      token: toText(defaultConfig.auth.config.token),
      headerName:
        toText(defaultConfig.auth.config.headerName) ||
        (defaultConfig.auth.type === "api_key_header"
          ? "x-api-key"
          : "X-Agent-Token"),
      secret: toText(defaultConfig.auth.config.secret),
    },
    platformInputMapping: {
      ...DEFAULT_INPUT_MAPPING,
      ...defaultConfig.platformInputMapping,
    },
    taskRenderMode: "goal_only",
    customRequestFields: customBodyToFields(defaultConfig.customRequestBody),
    requestOptions: normalizeRequestOptions(defaultConfig.requestOptions),
    platformOutputMapping: {
      ...DEFAULT_OUTPUT_MAPPING,
      ...defaultConfig.platformOutputMapping,
    },
    terminalStatusesText: defaultConfig.terminalStatuses.join(", "),
    successStatusesText: defaultConfig.successStatuses.join(", "),
  };
};

export const createAgentRegisterFormFromDetail = (
  detail: AgentDetail,
): AgentRegisterForm => {
  const headerName = toText(
    detail.auth.publicConfig?.headerName ?? detail.auth.config?.headerName,
  );

  return {
    templateId: detail.templateId,
    name: `${detail.name} 副本`,
    description: detail.description,
    invokeMode: detail.invokeMode,
    connection: normalizeConnection(detail.connection),
    auth: {
      type: detail.auth.type,
      token: "",
      headerName:
        headerName ||
        (detail.auth.type === "api_key_header" ? "x-api-key" : "X-Agent-Token"),
      secret: "",
    },
    platformInputMapping: {
      ...DEFAULT_INPUT_MAPPING,
      ...detail.platformInputMapping,
    },
    taskRenderMode: "goal_only",
    customRequestFields: customBodyToFields(detail.customRequestBody),
    requestOptions: normalizeRequestOptions(detail.requestOptions),
    platformOutputMapping: {
      ...DEFAULT_OUTPUT_MAPPING,
      ...detail.platformOutputMapping,
    },
    terminalStatusesText: detail.terminalStatuses.join(", "),
    successStatusesText: detail.successStatuses.join(", "),
  };
};

export const createEmptyAgentRegisterForm = (): AgentRegisterForm =>
  createAgentRegisterFormFromTemplate({
    templateId: "",
    name: "",
    description: "",
    recommended: false,
    sortOrder: 0,
    level: "basic",
    tags: [],
    defaultConfig: {
      invokeMode: "submit_poll",
      connection: DEFAULT_CONNECTION,
      auth: {
        type: "bearer",
        config: {
          token: "",
        },
      },
      platformInputMapping: DEFAULT_INPUT_MAPPING,
      taskRenderMode: "goal_only",
      customRequestBody: {},
      requestOptions: {
        structuredOutput: {
          supported: true,
          fieldAlias: "outputSchema",
        },
      },
      platformOutputMapping: DEFAULT_OUTPUT_MAPPING,
      terminalStatuses: ["completed", "failed", "timed_out"],
      successStatuses: ["completed"],
    },
  });

export const createCustomRequestField = (): AgentCustomRequestField => ({
  id: nextCustomFieldId(),
  key: "",
  valueType: "string",
  value: "",
});

export const selectDefaultTemplate = (
  templates: AgentTemplate[],
): AgentTemplate | null =>
  [...templates].sort(
    (left, right) =>
      Number(right.recommended) - Number(left.recommended) ||
      left.sortOrder - right.sortOrder,
  )[0] ?? null;

export const buildAgentCreatePayload = (
  form: AgentRegisterForm,
): AgentCreatePayloadResult => {
  const errors: string[] = [];
  const fieldErrors: AgentRegisterFieldErrors = {};
  const name = form.name.trim();

  if (!form.templateId.trim()) {
    errors.push("请选择注册模板。");
    fieldErrors.templateId = "请选择注册模板";
  }

  if (!name) {
    errors.push("请填写 Agent 名称。");
    fieldErrors.name = "请填写 Agent 名称";
  }

  if (!form.connection.baseUrl.trim()) {
    errors.push("请填写服务根地址。");
    fieldErrors.baseUrl = "请填写服务根地址";
  } else if (!isValidHttpUrl(form.connection.baseUrl.trim())) {
    errors.push("服务根地址格式不正确。");
    fieldErrors.baseUrl = "服务根地址格式不正确";
  }

  if (!form.connection.invokePath.trim()) {
    errors.push("请填写提交任务路径。");
    fieldErrors.invokePath = "请填写提交任务路径";
  }

  if (
    form.invokeMode === "submit_poll" &&
    !form.connection.resultPathTemplate?.trim()
  ) {
    errors.push("轮询模式下必须填写结果路径模板。");
    fieldErrors.resultPathTemplate = "请填写结果路径模板";
  }

  if (!form.platformInputMapping.task.trim()) {
    errors.push("平台任务字段映射不能为空。");
    fieldErrors.taskMapping = "请填写 task 对应字段名";
  }

  const customBodyResult = buildCustomRequestBody(form.customRequestFields);
  if (customBodyResult.errors.length) {
    errors.push(...customBodyResult.errors);
    fieldErrors.customRequestBody = customBodyResult.errors[0];
  }

  const mappedFieldNames = Object.values(form.platformInputMapping)
    .map((value) => value?.trim())
    .filter((value): value is string => Boolean(value));
  const mappedFieldNameSet = new Set(mappedFieldNames);
  const conflictField = Object.keys(customBodyResult.body).find((key) =>
    mappedFieldNameSet.has(key),
  );
  if (conflictField) {
    const message = `字段 ${conflictField} 已被平台输入映射使用，不能作为自定义固定字段。`;
    errors.push(message);
    fieldErrors.customRequestBody = message;
  }

  const terminalStatuses = parseStatusText(form.terminalStatusesText);
  const successStatuses = parseStatusText(form.successStatusesText);
  if (terminalStatuses.length === 0) {
    errors.push("请至少填写一个终态。");
    fieldErrors.terminalStatuses = "请至少填写一个终态";
  }

  const terminalStatusSet = new Set(terminalStatuses);
  const invalidSuccess = successStatuses.find(
    (item) => !terminalStatusSet.has(item),
  );
  if (invalidSuccess) {
    errors.push("成功态必须属于终态集合。");
    fieldErrors.successStatuses = "成功态必须属于终态集合";
  }

  if (
    form.invokeMode === "submit_poll" &&
    (!form.platformOutputMapping.externalRunId?.trim() ||
      !form.platformOutputMapping.status?.trim())
  ) {
    const message = "轮询模式下必须配置运行 ID 和状态输出路径。";
    errors.push(message);
    fieldErrors.outputMapping = message;
  }

  if (
    form.auth.type === "bearer" &&
    !form.auth.token.trim()
  ) {
    errors.push("请填写 Bearer Token。");
    fieldErrors.authSecret = "请填写 Bearer Token";
  }

  if (
    (form.auth.type === "api_key_header" ||
      form.auth.type === "custom_header") &&
    (!form.auth.headerName.trim() || !form.auth.secret.trim())
  ) {
    errors.push("请填写 Header 名称和密钥。");
    fieldErrors.authSecret = "请填写 Header 名称和密钥";
  }

  if (errors.length) {
    return {
      valid: false,
      errors,
      fieldErrors,
      payload: null,
    };
  }

  return {
    valid: true,
    errors: [],
    fieldErrors: {},
    payload: {
      templateId: form.templateId.trim(),
      name,
      description: form.description.trim(),
      invokeMode: form.invokeMode,
      connection: {
        ...form.connection,
        baseUrl: form.connection.baseUrl.trim(),
        invokePath: form.connection.invokePath.trim(),
        resultPathTemplate: form.connection.resultPathTemplate?.trim(),
      },
      auth: buildAuthConfig(form),
      platformInputMapping: cloneJson(form.platformInputMapping),
      taskRenderMode: "goal_only",
      customRequestBody: customBodyResult.body,
      requestOptions: cloneJson(form.requestOptions),
      platformOutputMapping: cloneJson(form.platformOutputMapping),
      terminalStatuses,
      successStatuses,
    },
  };
};

export const buildAgentInvocationPreview = (
  form: AgentRegisterForm,
): AgentInvocationPreview => {
  const baseUrl = form.connection.baseUrl.trim();
  const invokePath = form.connection.invokePath.trim();
  const customBody = buildCustomRequestBody(form.customRequestFields).body;
  const requestBody: Record<string, unknown> = { ...customBody };

  Object.entries(form.platformInputMapping).forEach(([platformField, target]) => {
    const targetField = target?.trim();
    if (!targetField) {
      return;
    }

    requestBody[targetField] =
      PLATFORM_INPUT_SAMPLES[platformField as keyof AgentInputMapping];
  });

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
  const authHeader = getAuthHeader(form);
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
