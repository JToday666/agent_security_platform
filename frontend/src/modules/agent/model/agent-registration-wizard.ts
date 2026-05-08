import type { AgentRegisterForm } from "./agent-registration-form";
import {
  validateAgentRegistration,
  type AgentRegisterFieldErrors,
} from "./agent-registration-validation";

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
    description: "指定平台字段和结构化输出配置写入请求体的位置。",
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
    description: "确认终态和成功态。",
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
  if (currentIndex < 0) {
    return null;
  }

  return steps[currentIndex + 1]?.id ?? null;
};

export const getPreviousAgentRegisterStep = (
  currentStep: AgentRegisterStepId,
  steps: AgentRegisterStep[],
): AgentRegisterStepId | null => {
  const currentIndex = steps.findIndex((step) => step.id === currentStep);
  if (currentIndex < 0) {
    return null;
  }

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

export const validateAgentRegisterStep = (
  stepId: AgentRegisterStepId,
  form: AgentRegisterForm,
): AgentRegisterStepValidationResult => {
  const result = validateAgentRegistration(form, stepId);

  return {
    valid: result.valid,
    errors: result.errors,
    fieldErrors: result.fieldErrors,
  };
};

export const hasAgentRegisterConfigurationInput = (
  form: AgentRegisterForm,
): boolean =>
  Boolean(
    form.connection.baseUrl.trim() ||
    form.connection.invokePath.trim() ||
    form.connection.resultPathTemplate?.trim() ||
    form.auth.token.trim() ||
    form.auth.headerName.trim() ||
    form.auth.secret.trim() ||
    Object.values(form.platformInputMapping).some((value) => value?.trim()) ||
    Object.values(form.platformOutputMapping).some((value) => value?.trim()) ||
    form.terminalStatusesText.trim() ||
    form.successStatusesText.trim() ||
    form.requestOptions.structuredOutput.supported ||
    form.requestOptions.structuredOutput.fieldAlias.trim() ||
    form.customRequestFields.some(
      (field) => field.key.trim() || field.value.trim(),
    ),
  );
