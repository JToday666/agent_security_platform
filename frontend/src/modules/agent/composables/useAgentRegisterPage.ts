import { computed, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import { useRoute, useRouter } from "vue-router";
import { RouteLocation } from "@/app/router/route-names";
import type { AppTranslator } from "@/app/i18n/runtime-translator";
import {
  createAgent,
  getAgentDetail,
  getAgentTemplates,
  verifyAgent,
} from "@/modules/agent/api/agent-api";
import {
  AGENT_NO_TEMPLATE_ID,
  buildAgentCreatePayload,
  buildAgentInvocationPreview,
  buildAgentRegisterSteps,
  createAgentRegisterFormFromDetail,
  createAgentRegisterFormFromTemplate,
  createCustomRequestField,
  createEmptyAgentRegisterForm,
  getNextAgentRegisterStep,
  getPreviousAgentRegisterStep,
  hasAgentRegisterConfigurationInput,
  shouldShowAgentRegisterPreview,
  validateAgentRegisterStep,
  type AgentCustomFieldType,
  type AgentRegisterFieldErrors,
  type AgentRegisterForm,
  type AgentRegisterStepId,
} from "@/modules/agent/model/agent-registration";
import type {
  AgentAuthType,
  AgentCancelMethod,
  AgentCreateResponse,
  AgentInputMapping,
  AgentOutputMapping,
  AgentTemplate,
} from "@/shared/types/agent-registry-types";
import { getErrorMessage } from "@/shared/composables/useAsyncState";

const authTypeValues: AgentAuthType[] = [
  "none",
  "bearer",
  "api_key_header",
  "custom_header",
];
const cancelMethodValues: AgentCancelMethod[] = ["POST", "DELETE", "PATCH"];
const customFieldTypeValues: AgentCustomFieldType[] = [
  "string",
  "number",
  "boolean",
  "json",
];

export const buildInvokeModeOptions = (t: AppTranslator) => [
  { label: t("agent.display.invokeModes.submitPoll"), value: "submit_poll" },
  {
    label: t("agent.display.invokeModes.syncResponse"),
    value: "sync_response",
  },
];

export const buildAuthOptions = (t: AppTranslator) => [
  { label: t("agent.auth.none"), value: "none" },
  { label: t("agent.auth.bearer"), value: "bearer" },
  { label: t("agent.auth.apiKeyHeader"), value: "api_key_header" },
  { label: t("agent.auth.customHeader"), value: "custom_header" },
];

export const buildCancelMethodOptions = () =>
  cancelMethodValues.map((value) => ({ label: value, value }));

export const buildCustomTypeOptions = (t: AppTranslator) => [
  { label: t("agent.registerForm.fieldTypes.string"), value: "string" },
  { label: t("agent.registerForm.fieldTypes.number"), value: "number" },
  { label: t("agent.registerForm.fieldTypes.boolean"), value: "boolean" },
  { label: t("agent.registerForm.fieldTypes.json"), value: "json" },
];

export const buildPreviewTabs = (t: AppTranslator) => [
  { label: "curl", value: "curl" as const },
  { label: "Python", value: "python" as const },
  { label: t("agent.preview.bodyTab"), value: "body" as const },
  { label: t("agent.preview.responseTab"), value: "response" as const },
];

export const buildInputMappingItems = (
  t: AppTranslator,
): Array<{
  key: keyof AgentInputMapping;
  label: string;
}> => [
  { key: "task", label: t("agent.registerForm.inputMappingLabels.task") },
  {
    key: "entryUrl",
    label: t("agent.registerForm.inputMappingLabels.entryUrl"),
  },
  {
    key: "timeoutSeconds",
    label: t("agent.registerForm.inputMappingLabels.timeoutSeconds"),
  },
  {
    key: "sampleId",
    label: t("agent.registerForm.inputMappingLabels.sampleId"),
  },
  {
    key: "evaluationId",
    label: t("agent.registerForm.inputMappingLabels.evaluationId"),
  },
  {
    key: "maxSteps",
    label: t("agent.registerForm.inputMappingLabels.maxSteps"),
  },
];

export const buildOutputMappingItems = (
  t: AppTranslator,
): Array<{
  key: keyof AgentOutputMapping;
  label: string;
}> => [
  {
    key: "externalRunId",
    label: t("agent.registerForm.outputMappingLabels.externalRunId"),
  },
  { key: "status", label: t("agent.registerForm.outputMappingLabels.status") },
  {
    key: "success",
    label: t("agent.registerForm.outputMappingLabels.success"),
  },
  {
    key: "finalAnswer",
    label: t("agent.registerForm.outputMappingLabels.finalAnswer"),
  },
  {
    key: "errorMessage",
    label: t("agent.registerForm.outputMappingLabels.errorMessage"),
  },
];

export type AgentPreviewTab = ReturnType<
  typeof buildPreviewTabs
>[number]["value"];
export type AgentRegisterCustomFieldsChoice = "unset" | "use" | "skip";

export const useAgentRegisterPage = () => {
  const route = useRoute();
  const router = useRouter();
  const { t } = useI18n();

  const templates = ref<AgentTemplate[]>([]);
  const form = ref<AgentRegisterForm>(createEmptyAgentRegisterForm());
  const loading = ref(true);
  const pageError = ref("");
  const submitError = ref("");
  const submitting = ref(false);
  const fieldErrors = ref<AgentRegisterFieldErrors>({});
  const createdAgent = ref<AgentCreateResponse | null>(null);
  const verifyingCreatedAgent = ref(false);
  const previewTab = ref<AgentPreviewTab>("curl");
  const currentStepId = ref<AgentRegisterStepId>("template");
  const completedStepIds = ref<AgentRegisterStepId[]>([]);
  const customFieldsChoice = ref<AgentRegisterCustomFieldsChoice>("unset");
  const templateChangeDialogVisible = ref(false);
  const pendingTemplateId = ref("");
  const copySourceLoaded = ref(false);
  const validationErrorVersion = ref(0);

  const preview = computed(() => buildAgentInvocationPreview(form.value, t));
  const previewCode = computed(() => {
    if (previewTab.value === "python") {
      return preview.value.python;
    }

    if (previewTab.value === "body") {
      return JSON.stringify(preview.value.requestBody, null, 2);
    }

    if (previewTab.value === "response") {
      return JSON.stringify(
        preview.value.responseMapping.responseBody,
        null,
        2,
      );
    }

    return preview.value.curl;
  });
  const previewLanguage = computed(() =>
    previewTab.value === "body" || previewTab.value === "response"
      ? "json"
      : previewTab.value,
  );
  const usesNoTemplate = computed(
    () => form.value.templateId === AGENT_NO_TEMPLATE_ID,
  );
  const selectedTemplate = computed(() =>
    templates.value.find(
      (template) => template.templateId === form.value.templateId,
    ),
  );
  const templateRequiresCustomFields = computed(() =>
    Boolean(
      selectedTemplate.value &&
      Object.keys(selectedTemplate.value.defaultConfig.customRequestBody)
        .length > 0,
    ),
  );
  const registerSteps = computed(() =>
    buildAgentRegisterSteps(
      {
        templateRequiresCustomFields: templateRequiresCustomFields.value,
        usesNoTemplate: usesNoTemplate.value,
      },
      t,
    ),
  );
  const currentStep = computed(
    () =>
      registerSteps.value.find((step) => step.id === currentStepId.value) ??
      registerSteps.value[0],
  );
  const isFirstStep = computed(
    () => registerSteps.value[0]?.id === currentStep.value?.id,
  );
  const isLastStep = computed(() => {
    const steps = registerSteps.value;
    return steps[steps.length - 1]?.id === currentStep.value?.id;
  });
  const showPreviewPanel = computed(() =>
    shouldShowAgentRegisterPreview(currentStepId.value),
  );
  const enterableStepIds = computed(() =>
    registerSteps.value.map((step) => step.id),
  );

  const markStepCompleted = (stepId: AgentRegisterStepId) => {
    if (!completedStepIds.value.includes(stepId)) {
      completedStepIds.value = [...completedStepIds.value, stepId];
    }
  };

  const clearCompletedAfter = (stepId: AgentRegisterStepId) => {
    const stepIndex = registerSteps.value.findIndex(
      (step) => step.id === stepId,
    );
    if (stepIndex < 0) {
      completedStepIds.value = [];
      return;
    }

    const retainedStepIds = new Set(
      registerSteps.value.slice(0, stepIndex + 1).map((step) => step.id),
    );
    completedStepIds.value = completedStepIds.value.filter((id) =>
      retainedStepIds.has(id),
    );
  };

  const clearCompletedFrom = (stepId: AgentRegisterStepId) => {
    const stepIndex = registerSteps.value.findIndex(
      (step) => step.id === stepId,
    );
    if (stepIndex < 0) {
      completedStepIds.value = [];
      return;
    }

    const retainedStepIds = new Set(
      registerSteps.value.slice(0, stepIndex).map((step) => step.id),
    );
    completedStepIds.value = completedStepIds.value.filter((id) =>
      retainedStepIds.has(id),
    );
  };

  const resetWizard = () => {
    currentStepId.value = "template";
    completedStepIds.value = [];
    customFieldsChoice.value = "unset";
    templateChangeDialogVisible.value = false;
    pendingTemplateId.value = "";
    copySourceLoaded.value = false;
  };

  const ensureCurrentStepVisible = () => {
    if (registerSteps.value.some((step) => step.id === currentStepId.value)) {
      return;
    }

    currentStepId.value =
      registerSteps.value[registerSteps.value.length - 1].id;
  };

  const updateCustomFieldsChoiceForTemplate = () => {
    if (usesNoTemplate.value) {
      customFieldsChoice.value = "unset";
      return;
    }

    customFieldsChoice.value = templateRequiresCustomFields.value
      ? "use"
      : "skip";
  };

  const initializePage = async () => {
    loading.value = true;
    pageError.value = "";
    submitError.value = "";
    createdAgent.value = null;
    fieldErrors.value = {};
    resetWizard();

    try {
      const loadedTemplates = await getAgentTemplates();
      templates.value = loadedTemplates;

      const copyFrom =
        typeof route.query.copyFrom === "string" ? route.query.copyFrom : "";
      if (copyFrom) {
        const detail = await getAgentDetail(copyFrom);
        form.value = createAgentRegisterFormFromDetail(detail, t);
        copySourceLoaded.value = true;
        updateCustomFieldsChoiceForTemplate();
        return;
      }

      form.value = createEmptyAgentRegisterForm();
    } catch (error) {
      pageError.value =
        getErrorMessage(error, t("agent.register.initFailed"));
    } finally {
      loading.value = false;
    }
  };

  const buildNoTemplateForm = (): AgentRegisterForm => {
    const nextForm = createEmptyAgentRegisterForm();
    nextForm.templateId = AGENT_NO_TEMPLATE_ID;
    return nextForm;
  };

  const applyTemplateImmediately = (templateId: string) => {
    if (createdAgent.value) {
      return;
    }

    const currentName = form.value.name;
    const currentDescription = form.value.description;

    if (templateId === AGENT_NO_TEMPLATE_ID) {
      form.value = buildNoTemplateForm();
      form.value.name = currentName;
      form.value.description = currentDescription;
      copySourceLoaded.value = false;
      fieldErrors.value = {};
      submitError.value = "";
      updateCustomFieldsChoiceForTemplate();
      clearCompletedAfter("template");
      ensureCurrentStepVisible();
      return;
    }

    const template = templates.value.find(
      (item) => item.templateId === templateId,
    );
    if (!template || createdAgent.value) {
      return;
    }

    form.value = createAgentRegisterFormFromTemplate(template);
    form.value.name = currentName;
    form.value.description = currentDescription;
    copySourceLoaded.value = false;
    fieldErrors.value = {};
    submitError.value = "";
    updateCustomFieldsChoiceForTemplate();
    clearCompletedAfter("template");
    ensureCurrentStepVisible();
  };

  const applyTemplate = (templateId: string) => {
    if (templateId === form.value.templateId || createdAgent.value) {
      return;
    }

    if (
      currentStepId.value !== "template" ||
      (copySourceLoaded.value && hasAgentRegisterConfigurationInput(form.value))
    ) {
      pendingTemplateId.value = templateId;
      templateChangeDialogVisible.value = true;
      return;
    }

    applyTemplateImmediately(templateId);
  };

  const confirmTemplateChange = () => {
    const nextTemplateId = pendingTemplateId.value;
    templateChangeDialogVisible.value = false;
    pendingTemplateId.value = "";
    if (nextTemplateId) {
      applyTemplateImmediately(nextTemplateId);
    }
  };

  const cancelTemplateChange = () => {
    templateChangeDialogVisible.value = false;
    pendingTemplateId.value = "";
  };

  const validateStepById = (stepId: AgentRegisterStepId): boolean => {
    if (
      stepId === "customFields" &&
      usesNoTemplate.value &&
      customFieldsChoice.value === "unset"
    ) {
      fieldErrors.value = {};
      submitError.value = t("agent.register.customFieldsChoiceRequired");
      validationErrorVersion.value += 1;
      return false;
    }

    const result = validateAgentRegisterStep(stepId, form.value, t);
    fieldErrors.value = result.fieldErrors;
    submitError.value = result.errors[0] || "";
    if (!result.valid) {
      validationErrorVersion.value += 1;
    }
    return result.valid;
  };

  const validateStepsUntil = (targetIndex: number): boolean => {
    const stepsToValidate = registerSteps.value.slice(0, targetIndex);
    for (const step of stepsToValidate) {
      if (!validateStepById(step.id)) {
        currentStepId.value = step.id;
        return false;
      }
      markStepCompleted(step.id);
    }

    return true;
  };

  const goToStep = (stepId: AgentRegisterStepId) => {
    if (!registerSteps.value.some((step) => step.id === stepId)) {
      return;
    }

    const currentIndex = registerSteps.value.findIndex(
      (step) => step.id === currentStepId.value,
    );
    const targetIndex = registerSteps.value.findIndex(
      (step) => step.id === stepId,
    );
    if (targetIndex > currentIndex) {
      if (!validateStepsUntil(targetIndex)) {
        return;
      }
    }

    currentStepId.value = stepId;
    submitError.value = "";
    fieldErrors.value = {};
  };

  const handleStepEdited = (stepId: AgentRegisterStepId) => {
    clearCompletedFrom(stepId);
    fieldErrors.value = {};
    submitError.value = "";
  };

  const setInvokeMode = (value: string) => {
    form.value.invokeMode =
      value === "sync_response" ? "sync_response" : "submit_poll";
    clearCompletedFrom("connection");
    fieldErrors.value = {};
    submitError.value = "";
  };

  const setAuthType = (value: string) => {
    const nextType = authTypeValues.includes(value as AgentAuthType)
      ? (value as AgentAuthType)
      : "none";
    clearCompletedFrom("connection");
    form.value.auth.type = nextType;
    fieldErrors.value = {};
    submitError.value = "";
  };

  const setCustomFieldType = (fieldId: string, value: string) => {
    const nextType = customFieldTypeValues.includes(
      value as AgentCustomFieldType,
    )
      ? (value as AgentCustomFieldType)
      : "string";
    const field = form.value.customRequestFields.find(
      (item) => item.id === fieldId,
    );
    if (field) {
      field.valueType = nextType;
    }
    clearCompletedFrom("customFields");
    fieldErrors.value = {};
    submitError.value = "";
  };

  const addCustomField = () => {
    form.value.customRequestFields.push(createCustomRequestField());
    clearCompletedFrom("customFields");
    fieldErrors.value = {};
    submitError.value = "";
  };

  const removeCustomField = (fieldId: string) => {
    form.value.customRequestFields = form.value.customRequestFields.filter(
      (field) => field.id !== fieldId,
    );
    clearCompletedFrom("customFields");
    fieldErrors.value = {};
    submitError.value = "";
  };

  const setCustomFieldsChoice = (choice: AgentRegisterCustomFieldsChoice) => {
    customFieldsChoice.value = choice;
    clearCompletedFrom("customFields");
    fieldErrors.value = {};
    submitError.value = "";

    if (choice === "skip") {
      form.value.customRequestFields = [];
      return;
    }

    if (choice === "use" && form.value.customRequestFields.length === 0) {
      addCustomField();
    }
  };

  const validateCurrentStep = (): boolean => {
    if (
      currentStepId.value === "customFields" &&
      usesNoTemplate.value &&
      customFieldsChoice.value === "unset"
    ) {
      fieldErrors.value = {};
      submitError.value = t("agent.register.customFieldsChoiceRequired");
      return false;
    }

    return validateStepById(currentStepId.value);
  };

  const goToNextStep = () => {
    if (!validateCurrentStep()) {
      return;
    }

    markStepCompleted(currentStepId.value);
    const nextStepId = getNextAgentRegisterStep(
      currentStepId.value,
      registerSteps.value,
    );
    if (nextStepId) {
      currentStepId.value = nextStepId;
      fieldErrors.value = {};
      submitError.value = "";
    }
  };

  const goToPreviousStep = () => {
    const previousStepId = getPreviousAgentRegisterStep(
      currentStepId.value,
      registerSteps.value,
    );
    if (previousStepId) {
      currentStepId.value = previousStepId;
      fieldErrors.value = {};
      submitError.value = "";
    }
  };

  const handleCreate = async () => {
    submitError.value = "";
    fieldErrors.value = {};
    const result = buildAgentCreatePayload(form.value, t);
    if (!result.valid || !result.payload) {
      fieldErrors.value = result.fieldErrors;
      submitError.value =
        result.errors[0] || t("agent.register.submitValidationFailed");
      validationErrorVersion.value += 1;
      return;
    }

    submitting.value = true;
    try {
      createdAgent.value = await createAgent(result.payload);
    } catch (error) {
      submitError.value =
        getErrorMessage(error, t("agent.api.createFailed"));
    } finally {
      submitting.value = false;
    }
  };

  const verifyCreatedAgent = async () => {
    if (!createdAgent.value) {
      return;
    }

    verifyingCreatedAgent.value = true;
    submitError.value = "";

    try {
      await verifyAgent(createdAgent.value.agentId);
      await router.push(RouteLocation.agentDetail(createdAgent.value.agentId));
    } catch (error) {
      submitError.value =
        getErrorMessage(error, t("agent.api.verifyFailed"));
    } finally {
      verifyingCreatedAgent.value = false;
    }
  };

  const copyPreview = async () => {
    if (!previewCode.value) {
      return;
    }

    await navigator.clipboard?.writeText(previewCode.value);
  };

  onMounted(async () => {
    await initializePage();
  });

  return {
    templates,
    form,
    loading,
    pageError,
    submitError,
    submitting,
    fieldErrors,
    createdAgent,
    verifyingCreatedAgent,
    previewTab,
    preview,
    previewCode,
    previewLanguage,
    currentStepId,
    currentStep,
    registerSteps,
    completedStepIds,
    enterableStepIds,
    isFirstStep,
    isLastStep,
    showPreviewPanel,
    customFieldsChoice,
    usesNoTemplate,
    templateChangeDialogVisible,
    validationErrorVersion,
    initializePage,
    applyTemplate,
    confirmTemplateChange,
    cancelTemplateChange,
    goToStep,
    goToNextStep,
    goToPreviousStep,
    setInvokeMode,
    setAuthType,
    setCustomFieldType,
    setCustomFieldsChoice,
    handleStepEdited,
    addCustomField,
    removeCustomField,
    handleCreate,
    verifyCreatedAgent,
    copyPreview,
  };
};
