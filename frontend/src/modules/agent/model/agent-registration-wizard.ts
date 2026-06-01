import {
  translateRuntimeMessage,
  type AppTranslator,
} from "@/app/i18n/runtime-translator";
import {
  AGENT_MAX_CONCURRENCY_DEFAULT,
  type AgentRegisterForm,
} from "./agent-registration-form";
import {
  validateAgentRegistration,
  type AgentRegisterFieldErrors,
} from "./agent-registration-validation";
export { AGENT_NO_TEMPLATE_ID } from "./agent-registration-constants";

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

const AGENT_REGISTER_STEP_IDS: AgentRegisterStepId[] = [
  "template",
  "basic",
  "connection",
  "inputMapping",
  "outputMapping",
  "customFields",
  "statuses",
];

export const buildAgentRegisterStepDefinitions = (
  t: AppTranslator = translateRuntimeMessage,
): AgentRegisterStep[] =>
  AGENT_REGISTER_STEP_IDS.map((id) => ({
    id,
    title: t(`agent.register.wizard.${id}.title`),
    description: t(`agent.register.wizard.${id}.description`),
  }));

export const buildAgentRegisterSteps = (
  {
    templateRequiresCustomFields,
    usesNoTemplate,
  }: AgentRegisterStepBuildOptions,
  t: AppTranslator = translateRuntimeMessage,
): AgentRegisterStep[] =>
  buildAgentRegisterStepDefinitions(t).filter(
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

export const validateAgentRegisterStep = (
  stepId: AgentRegisterStepId,
  form: AgentRegisterForm,
  t: AppTranslator = translateRuntimeMessage,
): AgentRegisterStepValidationResult => {
  const result = validateAgentRegistration(form, stepId, t);

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
    form.connection.cancelPathTemplate?.trim() ||
    form.maxConcurrency !== AGENT_MAX_CONCURRENCY_DEFAULT ||
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
