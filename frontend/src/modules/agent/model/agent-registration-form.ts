import {
  translateRuntimeMessage,
  type AppTranslator,
} from "@/app/i18n/runtime-translator";
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

const DEFAULT_CONNECTION: AgentConnectionConfig = {
  baseUrl: "",
  invokePath: "",
  resultPathTemplate: "",
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

const toInputMappingFormValue = (
  mapping: Partial<AgentInputMapping> = {},
): AgentInputMapping => ({
  task: toText(mapping.task),
  entryUrl: toText(mapping.entryUrl),
  timeoutSeconds: toText(mapping.timeoutSeconds),
  sampleId: toText(mapping.sampleId),
  evaluationId: toText(mapping.evaluationId),
  maxSteps: toText(mapping.maxSteps),
});

const toOutputMappingFormValue = (
  mapping: Partial<AgentOutputMapping> = {},
): AgentOutputMapping => ({
  externalRunId: toText(mapping.externalRunId),
  status: toText(mapping.status),
  finalAnswer: toText(mapping.finalAnswer),
  errorMessage: toText(mapping.errorMessage),
});

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
    fieldAlias: requestOptions?.structuredOutput?.supported
      ? toText(requestOptions.structuredOutput.fieldAlias)
      : "",
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
  t: AppTranslator = translateRuntimeMessage,
): { ok: true; value: unknown } | { ok: false; message: string } => {
  const value = field.value.trim();
  const fieldName = field.key || t("agent.common.customField");

  if (field.valueType === "string") {
    return { ok: true, value: field.value };
  }

  if (field.valueType === "number") {
    const parsed = Number(value);
    return Number.isFinite(parsed)
      ? { ok: true, value: parsed }
      : {
          ok: false,
          message: t("agent.validation.customFieldNumber", {
            field: fieldName,
          }),
        };
  }

  if (field.valueType === "boolean") {
    if (value === "true" || value === "false") {
      return { ok: true, value: value === "true" };
    }

    return {
      ok: false,
      message: t("agent.validation.customFieldBoolean", {
        field: fieldName,
      }),
    };
  }

  try {
    return { ok: true, value: JSON.parse(value) };
  } catch {
    return {
      ok: false,
      message: t("agent.validation.customFieldJson", {
        field: fieldName,
      }),
    };
  }
};

export const buildAgentCustomRequestBody = (
  fields: AgentCustomRequestField[],
  t: AppTranslator = translateRuntimeMessage,
): { body: Record<string, unknown>; errors: string[] } => {
  const body: Record<string, unknown> = {};
  const errors: string[] = [];

  fields.forEach((field) => {
    const key = field.key.trim();
    if (!key && !field.value.trim()) {
      return;
    }

    if (!key) {
      errors.push(t("agent.validation.customFieldKeyRequired"));
      return;
    }

    if (Object.prototype.hasOwnProperty.call(body, key)) {
      errors.push(t("agent.validation.customFieldDuplicate", { key }));
      return;
    }

    const parsed = parseCustomFieldValue(field, t);
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
      headerName: toText(defaultConfig.auth.config.headerName),
      secret: toText(defaultConfig.auth.config.secret),
    },
    platformInputMapping: toInputMappingFormValue(
      defaultConfig.platformInputMapping,
    ),
    taskRenderMode: "goal_only",
    customRequestFields: customBodyToFields(defaultConfig.customRequestBody),
    requestOptions: normalizeRequestOptions(defaultConfig.requestOptions),
    platformOutputMapping: toOutputMappingFormValue(
      defaultConfig.platformOutputMapping,
    ),
    terminalStatusesText: defaultConfig.terminalStatuses.join(", "),
    successStatusesText: defaultConfig.successStatuses.join(", "),
  };
};

export const createAgentRegisterFormFromDetail = (
  detail: AgentDetail,
  t: AppTranslator = translateRuntimeMessage,
): AgentRegisterForm => {
  const headerName = toText(
    detail.auth.publicConfig?.headerName ?? detail.auth.config?.headerName,
  );

  return {
    templateId: detail.templateId,
    name: t("agent.register.copyName", { name: detail.name }),
    description: detail.description,
    invokeMode: detail.invokeMode,
    connection: normalizeConnection(detail.connection),
    auth: {
      type: detail.auth.type,
      token: "",
      headerName,
      secret: "",
    },
    platformInputMapping: toInputMappingFormValue(detail.platformInputMapping),
    taskRenderMode: "goal_only",
    customRequestFields: customBodyToFields(detail.customRequestBody),
    requestOptions: normalizeRequestOptions(detail.requestOptions),
    platformOutputMapping: toOutputMappingFormValue(
      detail.platformOutputMapping,
    ),
    terminalStatusesText: detail.terminalStatuses.join(", "),
    successStatusesText: detail.successStatuses.join(", "),
  };
};

export const createEmptyAgentRegisterForm = (): AgentRegisterForm => ({
  templateId: "",
  name: "",
  description: "",
  invokeMode: "submit_poll",
  connection: {
    baseUrl: "",
    invokePath: "",
    resultPathTemplate: "",
    requestTimeoutSeconds: 30,
    pollIntervalSeconds: 2,
    pollTimeoutSeconds: 300,
  },
  auth: {
    type: "none",
    token: "",
    headerName: "",
    secret: "",
  },
  platformInputMapping: toInputMappingFormValue(),
  taskRenderMode: "goal_only",
  customRequestFields: [],
  requestOptions: {
    structuredOutput: {
      supported: false,
      fieldAlias: "",
    },
  },
  platformOutputMapping: toOutputMappingFormValue(),
  terminalStatusesText: "",
  successStatusesText: "",
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
