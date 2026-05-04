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
  buildAgentCreatePayload,
  buildAgentInvocationPreview,
  createAgentRegisterFormFromDetail,
  createAgentRegisterFormFromTemplate,
  createCustomRequestField,
  createEmptyAgentRegisterForm,
  selectDefaultTemplate,
  type AgentCustomFieldType,
  type AgentRegisterFieldErrors,
  type AgentRegisterForm,
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
  { key: "stepCount", label: "stepCount <- 响应路径" },
  { key: "artifacts", label: "artifacts <- 响应路径" },
];

export type AgentPreviewTab = (typeof previewTabs)[number]["value"];

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

  const preview = computed(() => buildAgentInvocationPreview(form.value));
  const previewCode = computed(() => {
    if (previewTab.value === "python") {
      return preview.value.python;
    }

    if (previewTab.value === "body") {
      return JSON.stringify(preview.value.requestBody, null, 2);
    }

    return preview.value.curl;
  });
  const previewLanguage = computed(() =>
    previewTab.value === "body" ? "json" : previewTab.value,
  );

  const initializePage = async () => {
    loading.value = true;
    pageError.value = "";
    submitError.value = "";
    createdAgent.value = null;
    fieldErrors.value = {};

    try {
      const loadedTemplates = await getAgentTemplates();
      templates.value = loadedTemplates;

      const copyFrom =
        typeof route.query.copyFrom === "string" ? route.query.copyFrom : "";
      if (copyFrom) {
        const detail = await getAgentDetail(copyFrom);
        form.value = createAgentRegisterFormFromDetail(detail);
        return;
      }

      const template = selectDefaultTemplate(loadedTemplates);
      form.value = template
        ? createAgentRegisterFormFromTemplate(template)
        : createEmptyAgentRegisterForm();
    } catch (error) {
      pageError.value =
        error instanceof Error ? error.message : "注册页初始化失败。";
    } finally {
      loading.value = false;
    }
  };

  const applyTemplate = (templateId: string) => {
    const template = templates.value.find(
      (item) => item.templateId === templateId,
    );
    if (!template || createdAgent.value) {
      return;
    }

    const currentName = form.value.name;
    const currentDescription = form.value.description;
    form.value = createAgentRegisterFormFromTemplate(template);
    form.value.name = currentName;
    form.value.description = currentDescription;
    fieldErrors.value = {};
  };

  const setInvokeMode = (value: string) => {
    form.value.invokeMode =
      value === "sync_response" ? "sync_response" : "submit_poll";
  };

  const setAuthType = (value: string) => {
    const nextType = authOptions.some((option) => option.value === value)
      ? (value as AgentAuthType)
      : "none";
    form.value.auth.type = nextType;
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
  };

  const addCustomField = () => {
    form.value.customRequestFields.push(createCustomRequestField());
  };

  const removeCustomField = (fieldId: string) => {
    form.value.customRequestFields = form.value.customRequestFields.filter(
      (field) => field.id !== fieldId,
    );
  };

  const handleCreate = async () => {
    submitError.value = "";
    fieldErrors.value = {};
    const result = buildAgentCreatePayload(form.value);
    if (!result.valid || !result.payload) {
      fieldErrors.value = result.fieldErrors;
      submitError.value = result.errors[0] || "Agent 创建参数校验失败。";
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
    initializePage,
    applyTemplate,
    setInvokeMode,
    setAuthType,
    setCustomFieldType,
    addCustomField,
    removeCustomField,
    handleCreate,
    verifyCreatedAgent,
    copyPreview,
  };
};
