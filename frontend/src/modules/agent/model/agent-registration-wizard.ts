import { isValidHttpUrl } from "@/modules/submission/model/parameter-validator";
import type { AgentRegisterFieldErrors } from "./agent-registration-payload";
import {
  buildAgentCustomRequestBody,
  parseAgentStatusText,
  type AgentRegisterForm,
} from "./agent-registration-form";

export const AGENT_NO_TEMPLATE_ID = "custom";

export type AgentRegisterStepId =
  | "template"
  | "basic"
  | "connection"
  | "inputMapping"
  | "outputMapping"
  | "customFields"
  | "statuses";

export interface AgentRegisterStep {
  id: AgentRegisterStepId;
  title: string;
  description: string;
}

export interface AgentRegisterStepBuildOptions {
  templateRequiresCustomFields: boolean;
  usesNoTemplate: boolean;
}

export interface AgentRegisterStepValidationResult {
  valid: boolean;
  errors: string[];
  fieldErrors: AgentRegisterFieldErrors;
}

export const AGENT_REGISTER_STEP_DEFINITIONS: AgentRegisterStep[] = [
  {
    id: "template",
    title: "选择模板",
    description: "选择预设模板或从空配置开始。",
  },
  {
    id: "basic",
    title: "基本信息",
    description: "填写名称和用途描述。",
  },
  {
    id: "connection",
    title: "连接与鉴权",
    description: "配置调用模式、服务地址和凭据。",
  },
  {
    id: "inputMapping",
    title: "输入字段映射",
    description: "指定平台字段写入请求体的位置。",
  },
  {
    id: "outputMapping",
    title: "输出字段映射",
    description: "指定平台从响应中读取结果的位置。",
  },
  {
    id: "customFields",
    title: "自定义固定字段",
    description: "配置每次请求都会附带的固定字段。",
  },
  {
    id: "statuses",
    title: "状态集合",
    description: "确认终态、成功态和结构化输出。",
  },
];

export const buildAgentRegisterSteps = ({
  templateRequiresCustomFields,
  usesNoTemplate,
}: AgentRegisterStepBuildOptions): AgentRegisterStep[] =>
  AGENT_REGISTER_STEP_DEFINITIONS.filter(
    (step) =>
      step.id !== "customFields" ||
      templateRequiresCustomFields ||
      usesNoTemplate,
  );

export const getNextAgentRegisterStep = (
  currentStep: AgentRegisterStepId,
  steps: AgentRegisterStep[],
): AgentRegisterStepId | null => {
  const currentIndex = steps.findIndex((step) => step.id === currentStep);
  return steps[currentIndex + 1]?.id ?? null;
};

export const getPreviousAgentRegisterStep = (
  currentStep: AgentRegisterStepId,
  steps: AgentRegisterStep[],
): AgentRegisterStepId | null => {
  const currentIndex = steps.findIndex((step) => step.id === currentStep);
  return currentIndex > 0 ? steps[currentIndex - 1].id : null;
};

export const shouldShowAgentRegisterPreview = (
  stepId: AgentRegisterStepId,
): boolean =>
  stepId === "connection" ||
  stepId === "inputMapping" ||
  stepId === "outputMapping" ||
  stepId === "customFields";

export const canEnterAgentRegisterStep = (
  targetStep: AgentRegisterStepId,
  steps: AgentRegisterStep[],
  completedSteps: AgentRegisterStepId[],
): boolean => {
  const targetIndex = steps.findIndex((step) => step.id === targetStep);
  if (targetIndex < 0) {
    return false;
  }

  const completedStepSet = new Set(completedSteps);
  const firstIncompleteIndex = steps.findIndex(
    (step) => !completedStepSet.has(step.id),
  );
  const maxAllowedIndex =
    firstIncompleteIndex === -1 ? steps.length - 1 : firstIncompleteIndex;

  return targetIndex <= maxAllowedIndex;
};

const pushFieldError = (
  errors: string[],
  fieldErrors: AgentRegisterFieldErrors,
  key: keyof AgentRegisterFieldErrors,
  message: string,
) => {
  errors.push(message);
  fieldErrors[key] = message;
};

const validateTemplateStep = (
  form: AgentRegisterForm,
  errors: string[],
  fieldErrors: AgentRegisterFieldErrors,
) => {
  if (!form.templateId.trim()) {
    pushFieldError(errors, fieldErrors, "templateId", "请选择注册模板");
  }
};

const validateBasicStep = (
  form: AgentRegisterForm,
  errors: string[],
  fieldErrors: AgentRegisterFieldErrors,
) => {
  if (!form.name.trim()) {
    pushFieldError(errors, fieldErrors, "name", "请填写 Agent 名称");
  }
};

const validateConnectionStep = (
  form: AgentRegisterForm,
  errors: string[],
  fieldErrors: AgentRegisterFieldErrors,
) => {
  if (!form.connection.baseUrl.trim()) {
    pushFieldError(errors, fieldErrors, "baseUrl", "请填写服务根地址");
  } else if (!isValidHttpUrl(form.connection.baseUrl.trim())) {
    pushFieldError(errors, fieldErrors, "baseUrl", "服务根地址格式不正确");
  }

  if (!form.connection.invokePath.trim()) {
    pushFieldError(errors, fieldErrors, "invokePath", "请填写提交任务路径");
  }

  if (
    form.invokeMode === "submit_poll" &&
    !form.connection.resultPathTemplate?.trim()
  ) {
    pushFieldError(
      errors,
      fieldErrors,
      "resultPathTemplate",
      "请填写结果路径模板",
    );
  }

  if (form.auth.type === "bearer" && !form.auth.token.trim()) {
    pushFieldError(errors, fieldErrors, "authSecret", "请填写 Bearer Token");
  }

  if (
    (form.auth.type === "api_key_header" ||
      form.auth.type === "custom_header") &&
    (!form.auth.headerName.trim() || !form.auth.secret.trim())
  ) {
    pushFieldError(errors, fieldErrors, "authSecret", "请填写 Header 名称和密钥");
  }
};

const validateInputMappingStep = (
  form: AgentRegisterForm,
  errors: string[],
  fieldErrors: AgentRegisterFieldErrors,
) => {
  if (!form.platformInputMapping.task.trim()) {
    pushFieldError(errors, fieldErrors, "taskMapping", "请填写 task 对应字段名");
  }
};

const validateOutputMappingStep = (
  form: AgentRegisterForm,
  errors: string[],
  fieldErrors: AgentRegisterFieldErrors,
) => {
  if (
    form.invokeMode === "submit_poll" &&
    (!form.platformOutputMapping.externalRunId?.trim() ||
      !form.platformOutputMapping.status?.trim())
  ) {
    pushFieldError(
      errors,
      fieldErrors,
      "outputMapping",
      "轮询模式下必须配置运行 ID 和状态输出路径。",
    );
  }
};

const validateCustomFieldsStep = (
  form: AgentRegisterForm,
  errors: string[],
  fieldErrors: AgentRegisterFieldErrors,
) => {
  const customBodyResult = buildAgentCustomRequestBody(form.customRequestFields);
  if (customBodyResult.errors.length) {
    pushFieldError(
      errors,
      fieldErrors,
      "customRequestBody",
      customBodyResult.errors[0],
    );
    return;
  }

  const mappedFieldNameSet = new Set(
    Object.values(form.platformInputMapping)
      .map((value) => value?.trim())
      .filter((value): value is string => Boolean(value)),
  );
  const conflictField = Object.keys(customBodyResult.body).find((key) =>
    mappedFieldNameSet.has(key),
  );
  if (conflictField) {
    pushFieldError(
      errors,
      fieldErrors,
      "customRequestBody",
      `字段 ${conflictField} 已被平台输入映射使用，不能作为自定义固定字段。`,
    );
  }
};

const validateStatusesStep = (
  form: AgentRegisterForm,
  errors: string[],
  fieldErrors: AgentRegisterFieldErrors,
) => {
  const terminalStatuses = parseAgentStatusText(form.terminalStatusesText);
  const successStatuses = parseAgentStatusText(form.successStatusesText);

  if (terminalStatuses.length === 0) {
    pushFieldError(errors, fieldErrors, "terminalStatuses", "请至少填写一个终态");
  }

  const terminalStatusSet = new Set(terminalStatuses);
  const invalidSuccess = successStatuses.find(
    (item) => !terminalStatusSet.has(item),
  );
  if (invalidSuccess) {
    pushFieldError(
      errors,
      fieldErrors,
      "successStatuses",
      "成功态必须属于终态集合",
    );
  }
};

export const validateAgentRegisterStep = (
  stepId: AgentRegisterStepId,
  form: AgentRegisterForm,
): AgentRegisterStepValidationResult => {
  const errors: string[] = [];
  const fieldErrors: AgentRegisterFieldErrors = {};

  if (stepId === "template") {
    validateTemplateStep(form, errors, fieldErrors);
  } else if (stepId === "basic") {
    validateBasicStep(form, errors, fieldErrors);
  } else if (stepId === "connection") {
    validateConnectionStep(form, errors, fieldErrors);
  } else if (stepId === "inputMapping") {
    validateInputMappingStep(form, errors, fieldErrors);
  } else if (stepId === "outputMapping") {
    validateOutputMappingStep(form, errors, fieldErrors);
  } else if (stepId === "customFields") {
    validateCustomFieldsStep(form, errors, fieldErrors);
  } else if (stepId === "statuses") {
    validateStatusesStep(form, errors, fieldErrors);
  }

  return {
    valid: errors.length === 0,
    errors,
    fieldErrors,
  };
};

export const hasAgentRegisterConfigurationInput = (
  form: AgentRegisterForm,
): boolean =>
  Boolean(
    form.connection.baseUrl.trim() ||
      form.auth.token.trim() ||
      form.auth.secret.trim() ||
      form.customRequestFields.some(
        (field) => field.key.trim() || field.value.trim(),
      ),
  );
