import {
  translateRuntimeMessage,
  type AppTranslator,
} from "@/app/i18n/runtime-translator";
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

const inputMappingTopLevelMessage = (t: AppTranslator) =>
  t("agent.validation.inputMappingTopLevel");
const outputMappingPathMessage = (t: AppTranslator) =>
  t("agent.validation.outputMappingPath");

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
  t: AppTranslator = translateRuntimeMessage,
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
      message: outputMappingPathMessage(t),
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
  t: AppTranslator = translateRuntimeMessage,
): AgentRegistrationValidationResult => {
  const errors: string[] = [];
  const fieldErrors: AgentRegisterFieldErrors = {};
  const normalized = buildNormalizedRegistration(form);

  if (shouldValidateSection(scope, "template") && !normalized.templateId) {
    addFieldError(
      errors,
      fieldErrors,
      "templateId",
      t("agent.validation.templateRequired"),
    );
  }

  if (shouldValidateSection(scope, "basic") && !normalized.name) {
    addFieldError(
      errors,
      fieldErrors,
      "name",
      t("agent.validation.nameRequired"),
    );
  }

  if (shouldValidateSection(scope, "connection")) {
    if (!normalized.connection.baseUrl) {
      addFieldError(
        errors,
        fieldErrors,
        "baseUrl",
        t("agent.validation.baseUrlRequired"),
      );
    } else if (!isValidHttpUrl(normalized.connection.baseUrl)) {
      addFieldError(
        errors,
        fieldErrors,
        "baseUrl",
        t("agent.validation.baseUrlInvalid"),
      );
    }

    if (!normalized.connection.invokePath) {
      addFieldError(
        errors,
        fieldErrors,
        "invokePath",
        t("agent.validation.invokePathRequired"),
      );
    }

    if (
      form.invokeMode === "submit_poll" &&
      !normalized.connection.resultPathTemplate
    ) {
      addFieldError(
        errors,
        fieldErrors,
        "resultPathTemplate",
        t("agent.validation.resultPathTemplateRequired"),
      );
    }

    if (form.auth.type === "bearer" && !form.auth.token.trim()) {
      addFieldError(
        errors,
        fieldErrors,
        "authSecret",
        t("agent.validation.authSecretRequired"),
      );
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
          t("agent.validation.authHeaderNameRequired"),
        );
      }

      if (!form.auth.secret.trim()) {
        addFieldError(
          errors,
          fieldErrors,
          "authHeaderSecret",
          t("agent.validation.authHeaderSecretRequired"),
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
        t("agent.validation.taskMappingRequired"),
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
          inputMappingTopLevelMessage(t),
        );
      }
    }

    if (form.requestOptions.structuredOutput.supported) {
      if (!normalized.requestOptions.structuredOutput.fieldAlias) {
        addFieldError(
          errors,
          fieldErrors,
          "structuredOutputAlias",
          t("agent.validation.structuredOutputAliasRequired"),
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
          t("agent.validation.structuredOutputAliasInvalid"),
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
        t("agent.validation.pollOutputRequired"),
      );
    }

    const invalidOutputMapping = Object.values(
      normalized.platformOutputMapping,
    ).find((path) => !parseAgentOutputJsonPath(path, t).valid);
    if (invalidOutputMapping) {
      addFieldError(
        errors,
        fieldErrors,
        "outputMapping",
        outputMappingPathMessage(t),
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
          t("agent.validation.customFieldMappingConflict", {
            field: conflictField,
          }),
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
        t("agent.validation.terminalStatusRequired"),
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
        t("agent.validation.statusSuccessInTerminal"),
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
