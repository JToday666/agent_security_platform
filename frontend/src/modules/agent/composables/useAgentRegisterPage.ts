import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { RouteLocation } from "@/app/router/route-names";
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
  AgentCreateResponse,
  AgentInputMapping,
  AgentOutputMapping,
  AgentTemplate,
} from "@/shared/types/agent-registry-types";

export const invokeModeOptions = [
  { label: "提交轮询", value: "submit_poll" },
  { label: "同步响应", value: "sync_response" },
];

export const authOptions = [
  { label: "不使用鉴权", value: "none" },
  { label: "Bearer Token", value: "bearer" },
  { label: "API Key Header", value: "api_key_header" },
  { label: "自定义 Header", value: "custom_header" },
];

export const customTypeOptions = [
  { label: "字符串", value: "string" },
  { label: "数字", value: "number" },
  { label: "布尔值", value: "boolean" },
  { label: "JSON", value: "json" },
];

export const previewTabs = [
  { label: "curl", value: "curl" as const },
  { label: "Python", value: "python" as const },
  { label: "请求体", value: "body" as const },
  { label: "响应解析", value: "response" as const },
];

export const inputMappingItems: Array<{
  key: keyof AgentInputMapping;
  label: string;
}> = [
  { key: "task", label: "task -> Agent 字段" },
  { key: "entryUrl", label: "entryUrl -> Agent 字段" },
  { key: "timeoutSeconds", label: "timeoutSeconds -> Agent 字段" },
  { key: "sampleId", label: "sampleId -> Agent 字段" },
  { key: "evaluationId", label: "evaluationId -> Agent 字段" },
  { key: "maxSteps", label: "maxSteps -> Agent 字段" },
];

export const outputMappingItems: Array<{
  key: keyof AgentOutputMapping;
  label: string;
}> = [
  { key: "externalRunId", label: "externalRunId <- 响应路径" },
  { key: "status", label: "status <- 响应路径" },
  { key: "finalAnswer", label: "finalAnswer <- 响应路径" },
  { key: "errorMessage", label: "errorMessage <- 响应路径" },
];

export type AgentPreviewTab = (typeof previewTabs)[number]["value"];
export type AgentRegisterCustomFieldsChoice = "unset" | "use" | "skip";

export const useAgentRegisterPage = () => {
  const route = useRoute();
  const router = useRouter();

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

  const preview = computed(() => buildAgentInvocationPreview(form.value));
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
    buildAgentRegisterSteps({
      templateRequiresCustomFields: templateRequiresCustomFields.value,
      usesNoTemplate: usesNoTemplate.value,
    }),
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
        form.value = createAgentRegisterFormFromDetail(detail);
        copySourceLoaded.value = true;
        updateCustomFieldsChoiceForTemplate();
        return;
      }

      form.value = createEmptyAgentRegisterForm();
    } catch (error) {
      pageError.value =
        error instanceof Error ? error.message : "注册页初始化失败。";
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
      submitError.value = "请选择是否添加自定义固定字段。";
      validationErrorVersion.value += 1;
      return false;
    }

    const result = validateAgentRegisterStep(stepId, form.value);
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
    const nextType = authOptions.some((option) => option.value === value)
      ? (value as AgentAuthType)
      : "none";
    clearCompletedFrom("connection");
    form.value.auth.type = nextType;
    fieldErrors.value = {};
    submitError.value = "";
  };

  const setCustomFieldType = (fieldId: string, value: string) => {
    const nextType = customTypeOptions.some((option) => option.value === value)
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
      submitError.value = "请选择是否添加自定义固定字段。";
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
    const result = buildAgentCreatePayload(form.value);
    if (!result.valid || !result.payload) {
      fieldErrors.value = result.fieldErrors;
      submitError.value = result.errors[0] || "Agent 创建参数校验失败。";
      validationErrorVersion.value += 1;
      return;
    }

    submitting.value = true;
    try {
      createdAgent.value = await createAgent(result.payload);
    } catch (error) {
      submitError.value =
        error instanceof Error ? error.message : "Agent 创建失败。";
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
        error instanceof Error ? error.message : "Agent 验证失败。";
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
