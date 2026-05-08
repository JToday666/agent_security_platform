import { isValidHttpUrl } from "@/modules/submission/model/parameter-validator";
import type {
  AgentAuthType,
  AgentConnectionConfig,
  AgentInputMapping,
  AgentOutputMapping,
  AgentRequestOptions,
} from "@/shared/types/agent-registry-types";
import {
  buildAgentCustomRequestBody,
  cloneAgentRegistrationJson,
  parseAgentStatusText,
  type AgentRegisterForm,
} from "./agent-registration-form";

export interface AgentRegisterFieldErrors {
  templateId?: string;
  name?: string;
  baseUrl?: string;
  invokePath?: string;
  resultPathTemplate?: string;
  taskMapping?: string;
  structuredOutputAlias?: string;
  customRequestBody?: string;
  outputMapping?: string;
  terminalStatuses?: string;
  successStatuses?: string;
  authSecret?: string;
  authHeaderName?: string;
  authHeaderSecret?: string;
}

export type AgentRegistrationValidationSection =
  | "template"
  | "basic"
  | "connection"
  | "inputMapping"
  | "outputMapping"
  | "customFields"
  | "statuses";

export type AgentRegistrationValidationScope =
  | "all"
  | AgentRegistrationValidationSection;

export interface NormalizedAgentRegistration {
  templateId: string;
  name: string;
  description: string;
  connection: AgentConnectionConfig;
  auth: { type: AgentAuthType; config: Record<string, string> };
  platformInputMapping: AgentInputMapping;
  customRequestBody: Record<string, unknown>;
  requestOptions: AgentRequestOptions;
  platformOutputMapping: AgentOutputMapping;
  terminalStatuses: string[];
  successStatuses: string[];
}

export interface AgentRegistrationValidationResult {
  valid: boolean;
  errors: string[];
  fieldErrors: AgentRegisterFieldErrors;
  normalized: NormalizedAgentRegistration;
}

const optionalInputMappingKeys: Array<
  Exclude<keyof AgentInputMapping, "task">
> = ["entryUrl", "timeoutSeconds", "sampleId", "evaluationId", "maxSteps"];

export const agentOutputMappingKeys: Array<keyof AgentOutputMapping> = [
  "externalRunId",
  "status",
  "finalAnswer",
  "errorMessage",
];

const inputMappingTopLevelMessage =
  "平台输入映射只能填写外部请求体的顶层字段名";
const outputMappingPathMessage =
  "输出映射需填写响应字段路径，例如 runId 或 data.runId，暂不支持 $、数组下标或空路径段。";

const addFieldError = (
  errors: string[],
  fieldErrors: AgentRegisterFieldErrors,
  key: keyof AgentRegisterFieldErrors,
  message: string,
) => {
  errors.push(message);
  fieldErrors[key] = message;
};

const shouldValidateSection = (
  scope: AgentRegistrationValidationScope,
  section: AgentRegistrationValidationSection,
): boolean => scope === "all" || scope === section;

export const isTopLevelAgentInputFieldName = (value: string): boolean =>
  Boolean(value) && !/[.[\]]/.test(value);

export interface AgentOutputJsonPathParseResult {
  valid: boolean;
  normalized: string;
  segments: string[];
  message: string;
}

export const parseAgentOutputJsonPath = (
  value: string,
): AgentOutputJsonPathParseResult => {
  const normalized = value.trim();
  const segments = normalized.split(".");
  const hasInvalidSyntax =
    !normalized ||
    normalized.startsWith("$") ||
    normalized.includes("[") ||
    normalized.includes("]") ||
    segments.some(
      (segment) =>
        !segment || segment !== segment.trim() || segment.includes("$"),
    );

  if (hasInvalidSyntax) {
    return {
      valid: false,
      normalized,
      segments: [],
      message: outputMappingPathMessage,
    };
  }

  return {
    valid: true,
    normalized,
    segments,
    message: "",
  };
};

export const normalizeAgentInputMapping = (
  mapping: AgentInputMapping,
): AgentInputMapping => {
  const normalized: AgentInputMapping = {
    task: mapping.task?.trim() ?? "",
  };

  optionalInputMappingKeys.forEach((key) => {
    const value = mapping[key]?.trim();
    if (value) {
      normalized[key] = value;
    }
  });

  return normalized;
};

export const normalizeAgentOutputMapping = (
  mapping: AgentOutputMapping,
): AgentOutputMapping => {
  const normalized: AgentOutputMapping = {};

  agentOutputMappingKeys.forEach((key) => {
    const value = mapping[key]?.trim();
    if (value) {
      normalized[key] = value;
    }
  });

  return normalized;
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

const normalizeConnection = (
  connection: AgentConnectionConfig,
): AgentConnectionConfig => ({
  ...connection,
  baseUrl: connection.baseUrl.trim(),
  invokePath: connection.invokePath.trim(),
  resultPathTemplate: connection.resultPathTemplate?.trim() || undefined,
  requestTimeoutSeconds: Number(connection.requestTimeoutSeconds),
  pollIntervalSeconds: Number(connection.pollIntervalSeconds),
  pollTimeoutSeconds: Number(connection.pollTimeoutSeconds),
});

const normalizeRequestOptions = (
  requestOptions: AgentRequestOptions,
): AgentRequestOptions => ({
  structuredOutput: {
    supported: Boolean(requestOptions.structuredOutput.supported),
    fieldAlias: requestOptions.structuredOutput.supported
      ? requestOptions.structuredOutput.fieldAlias.trim()
      : "",
  },
});

const buildNormalizedRegistration = (
  form: AgentRegisterForm,
): NormalizedAgentRegistration => ({
  templateId: form.templateId.trim(),
  name: form.name.trim(),
  description: form.description.trim(),
  connection: normalizeConnection(form.connection),
  auth: buildAuthConfig(form),
  platformInputMapping: normalizeAgentInputMapping(form.platformInputMapping),
  customRequestBody: buildAgentCustomRequestBody(form.customRequestFields).body,
  requestOptions: normalizeRequestOptions(
    cloneAgentRegistrationJson(form.requestOptions),
  ),
  platformOutputMapping: normalizeAgentOutputMapping(
    form.platformOutputMapping,
  ),
  terminalStatuses: parseAgentStatusText(form.terminalStatusesText),
  successStatuses: parseAgentStatusText(form.successStatusesText),
});

export const validateAgentRegistration = (
  form: AgentRegisterForm,
  scope: AgentRegistrationValidationScope = "all",
): AgentRegistrationValidationResult => {
  const errors: string[] = [];
  const fieldErrors: AgentRegisterFieldErrors = {};
  const normalized = buildNormalizedRegistration(form);

  if (shouldValidateSection(scope, "template") && !normalized.templateId) {
    addFieldError(errors, fieldErrors, "templateId", "请选择注册模板");
  }

  if (shouldValidateSection(scope, "basic") && !normalized.name) {
    addFieldError(errors, fieldErrors, "name", "请填写 Agent 名称");
  }

  if (shouldValidateSection(scope, "connection")) {
    if (!normalized.connection.baseUrl) {
      addFieldError(errors, fieldErrors, "baseUrl", "请填写服务根地址");
    } else if (!isValidHttpUrl(normalized.connection.baseUrl)) {
      addFieldError(errors, fieldErrors, "baseUrl", "服务根地址格式不正确");
    }

    if (!normalized.connection.invokePath) {
      addFieldError(errors, fieldErrors, "invokePath", "请填写提交任务路径");
    }

    if (
      form.invokeMode === "submit_poll" &&
      !normalized.connection.resultPathTemplate
    ) {
      addFieldError(
        errors,
        fieldErrors,
        "resultPathTemplate",
        "请填写结果路径模板",
      );
    }

    if (form.auth.type === "bearer" && !form.auth.token.trim()) {
      addFieldError(errors, fieldErrors, "authSecret", "请填写 Bearer Token");
    }

    if (
      form.auth.type === "api_key_header" ||
      form.auth.type === "custom_header"
    ) {
      if (!form.auth.headerName.trim()) {
        addFieldError(
          errors,
          fieldErrors,
          "authHeaderName",
          "请填写 Header 名称",
        );
      }

      if (!form.auth.secret.trim()) {
        addFieldError(
          errors,
          fieldErrors,
          "authHeaderSecret",
          "请填写 Header 密钥",
        );
      }
    }
  }

  if (shouldValidateSection(scope, "inputMapping")) {
    if (!normalized.platformInputMapping.task) {
      addFieldError(
        errors,
        fieldErrors,
        "taskMapping",
        "请填写 task 对应字段名",
      );
    } else {
      const invalidInputMapping = Object.values(
        normalized.platformInputMapping,
      ).find((value) => !isTopLevelAgentInputFieldName(value));
      if (invalidInputMapping) {
        addFieldError(
          errors,
          fieldErrors,
          "taskMapping",
          inputMappingTopLevelMessage,
        );
      }
    }

    if (form.requestOptions.structuredOutput.supported) {
      if (!normalized.requestOptions.structuredOutput.fieldAlias) {
        addFieldError(
          errors,
          fieldErrors,
          "structuredOutputAlias",
          "请填写结构化输出字段别名",
        );
      } else if (
        !isTopLevelAgentInputFieldName(
          normalized.requestOptions.structuredOutput.fieldAlias,
        )
      ) {
        addFieldError(
          errors,
          fieldErrors,
          "structuredOutputAlias",
          "结构化输出字段别名只能填写请求体顶层字段名",
        );
      }
    }
  }

  if (shouldValidateSection(scope, "outputMapping")) {
    if (
      form.invokeMode === "submit_poll" &&
      (!normalized.platformOutputMapping.externalRunId ||
        !normalized.platformOutputMapping.status)
    ) {
      addFieldError(
        errors,
        fieldErrors,
        "outputMapping",
        "轮询模式下必须配置运行 ID 和状态输出路径。",
      );
    }

    const invalidOutputMapping = Object.values(
      normalized.platformOutputMapping,
    ).find((path) => !parseAgentOutputJsonPath(path).valid);
    if (invalidOutputMapping) {
      addFieldError(
        errors,
        fieldErrors,
        "outputMapping",
        outputMappingPathMessage,
      );
    }
  }

  if (shouldValidateSection(scope, "customFields")) {
    const customBodyResult = buildAgentCustomRequestBody(
      form.customRequestFields,
    );
    if (customBodyResult.errors.length) {
      addFieldError(
        errors,
        fieldErrors,
        "customRequestBody",
        customBodyResult.errors[0],
      );
    } else {
      const mappedFieldNameSet = new Set(
        Object.values(normalized.platformInputMapping),
      );
      const conflictField = Object.keys(customBodyResult.body).find((key) =>
        mappedFieldNameSet.has(key),
      );
      if (conflictField) {
        addFieldError(
          errors,
          fieldErrors,
          "customRequestBody",
          `字段 ${conflictField} 已被平台输入映射使用，不能作为自定义固定字段。`,
        );
      }
    }
  }

  if (shouldValidateSection(scope, "statuses")) {
    if (normalized.terminalStatuses.length === 0) {
      addFieldError(
        errors,
        fieldErrors,
        "terminalStatuses",
        "请至少填写一个终态",
      );
    }

    const terminalStatusSet = new Set(normalized.terminalStatuses);
    const invalidSuccess = normalized.successStatuses.find(
      (item) => !terminalStatusSet.has(item),
    );
    if (invalidSuccess) {
      addFieldError(
        errors,
        fieldErrors,
        "successStatuses",
        "成功态必须属于终态集合",
      );
    }
  }

  return {
    valid: errors.length === 0,
    errors,
    fieldErrors,
    normalized,
  };
};
