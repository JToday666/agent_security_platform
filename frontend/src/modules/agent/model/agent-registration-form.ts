import type {
  AgentAuthType,
  AgentConnectionConfig,
  AgentDetail,
  AgentInputMapping,
  AgentInvokeMode,
  AgentOutputMapping,
  AgentRequestOptions,
  AgentTemplate,
} from "@/shared/types/agent-registry-types";

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

export const DEFAULT_INPUT_MAPPING: AgentInputMapping = {
  task: "task",
  entryUrl: "entryUrl",
  timeoutSeconds: "timeoutSeconds",
  sampleId: "sampleId",
  evaluationId: "evaluationId",
  maxSteps: "maxSteps",
};

export const DEFAULT_OUTPUT_MAPPING: AgentOutputMapping = {
  externalRunId: "data.runId",
  status: "data.status",
  finalAnswer: "data.answer",
  errorMessage: "data.error.message",
  stepCount: "data.metrics.stepCount",
  artifacts: "data.artifacts",
};

const DEFAULT_CONNECTION: AgentConnectionConfig = {
  baseUrl: "",
  invokePath: "/api/runs",
  resultPathTemplate: "/api/runs/{externalRunId}",
  requestTimeoutSeconds: 30,
  pollIntervalSeconds: 2,
  pollTimeoutSeconds: 300,
};

let customFieldIdSeed = 0;

const nextCustomFieldId = (): string => {
  customFieldIdSeed += 1;
  return `field_${customFieldIdSeed}`;
};

const toText = (value: unknown): string =>
  typeof value === "string" ? value.trim() : "";

export const cloneAgentRegistrationJson = <T>(value: T): T =>
  JSON.parse(JSON.stringify(value)) as T;

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

export const parseAgentStatusText = (value: string): string[] =>
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

export const buildAgentCustomRequestBody = (
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

export const getAgentAuthHeader = (
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
