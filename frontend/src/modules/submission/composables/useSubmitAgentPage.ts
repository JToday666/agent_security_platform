import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { storeToRefs } from "pinia";
import { useRoute, useRouter } from "vue-router";
import { RouteLocation } from "@/app/router/route-names";
import {
  getSubmitMeta,
  precheckAgent,
  submitAgent,
} from "@/modules/evaluation/api/evaluation-api";
import { getAgents } from "@/modules/agent/api/agent-api";
import { getAgentSubmitDisabledReason } from "@/modules/agent/model/agent-display";
import {
  toggleCategoryDatasets as toggleCategoryDatasetsValue,
  toggleDatasetId,
} from "@/modules/dataset/lib/dataset-utils";
import { useSubmitDraftStore } from "@/modules/submission/stores/submitDraftStore";
import { useSubmitDatasetCatalog } from "./useSubmitDatasetCatalog";
import {
  MAX_SUBMIT_DATASET_COUNT,
  normalizeDifficulty,
  normalizeMaxSteps,
  normalizeTimeoutMinutes,
  validateSubmitPayload,
} from "@/modules/submission/model/parameter-validator";
import { filterAvailableSubmitAgents } from "@/modules/submission/model/submit-agent-options";
import { resolveDatasetIdsFromQuery } from "@/modules/submission/lib/submit-query-utils";
import type {
  PendingSubmitRequest,
  SubmitAgentPayload,
  SubmitFieldErrors,
  SubmitMetaResponse,
} from "@/shared/types/agent-types";
import type { AgentListItem } from "@/shared/types/agent-registry-types";
import { useAsyncState } from "@/shared/composables/useAsyncState";

interface SubmitPayloadSnapshot {
  submitMethod: SubmitAgentPayload["submitMethod"];
  agentId: string;
  parameters: SubmitAgentPayload["parameters"];
  publicToLeaderboard: boolean;
  datasetIds: string[];
}

const buildRequestId = (): string => {
  if (
    typeof crypto !== "undefined" &&
    typeof crypto.randomUUID === "function"
  ) {
    return `submit_${crypto.randomUUID()}`;
  }

  return `submit_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
};

const isAbortLikeError = (error: unknown): boolean =>
  error instanceof DOMException
    ? error.name === "AbortError"
    : error instanceof Error
      ? error.name === "AbortError" || error.name === "CanceledError"
      : false;

const buildDatasetQuerySignature = (
  value: string | string[] | null | undefined,
): string => {
  if (!value) {
    return "";
  }

  return Array.isArray(value) ? value.join(",") : value;
};

export const useSubmitAgentPage = () => {
  const route = useRoute();
  const router = useRouter();
  const submitDraftStore = useSubmitDraftStore();
  const datasetCatalog = useSubmitDatasetCatalog();
  const datasetCatalogStatus = datasetCatalog.status;
  const datasetCatalogErrorMessage = datasetCatalog.errorMessage;

  const { form, expandedCategoryIds, pendingRequest } =
    storeToRefs(submitDraftStore);

  const {
    data: submitMeta,
    loading: pageLoading,
    error: pageError,
    startLoading,
    stopLoading,
    setError,
  } = useAsyncState<SubmitMetaResponse>();

  const {
    loading: submitting,
    error: submitError,
    startLoading: startSubmitting,
    stopLoading: stopSubmitting,
    setError: setSubmitError,
  } = useAsyncState<void>();

  const agents = ref<AgentListItem[]>([]);
  const fieldErrors = ref<SubmitFieldErrors>({});
  const datasetSelectionNotice = ref("");
  const agentSelectionNotice = ref("");
  const confirmDialogVisible = ref(false);
  const confirmDialogTitle = ref("确认提交");
  const confirmDialogMessage = ref("");
  const confirmedPayload = ref<SubmitAgentPayload | null>(null);

  let activeCatalogController: AbortController | null = null;
  let appliedDatasetQuerySignature = "";
  let appliedAgentQueryValue = "";

  const enabledCategories = computed(
    () => datasetCatalog.enabledCategories.value,
  );
  const validDatasetIds = computed(() => datasetCatalog.datasetIds.value);
  const datasetCatalogReady = computed(
    () => datasetCatalogStatus.value === "ready",
  );
  const availableAgents = computed(() =>
    filterAvailableSubmitAgents(agents.value),
  );
  const activeAgentIds = computed(() =>
    availableAgents.value.map((agent) => agent.agentId),
  );
  const selectedAgent = computed(() => {
    const agentId = form.value?.agentId;
    if (!agentId) {
      return null;
    }

    return availableAgents.value.find((agent) => agent.agentId === agentId) ?? null;
  });
  const selectedAgentSubmitDisabledReason = computed(() =>
    selectedAgent.value ? getAgentSubmitDisabledReason(selectedAgent.value) : "",
  );
  const selectedCategoryCount = computed(
    () =>
      enabledCategories.value.filter((category) =>
        category.subcategories.some((item) =>
          form.value?.selectedDatasetIds.includes(item.datasetId),
        ),
      ).length,
  );
  const selectedDatasetNames = computed(() => {
    if (!form.value) {
      return [];
    }

    const nameById = new Map(
      enabledCategories.value.flatMap((category) =>
        category.subcategories.map(
          (dataset) => [dataset.datasetId, dataset.name] as const,
        ),
      ),
    );

    return form.value.selectedDatasetIds
      .map((datasetId) => nameById.get(datasetId))
      .filter((name): name is string => Boolean(name));
  });
  const selectionErrorMessage = computed(
    () => fieldErrors.value.selectedDatasetIds || datasetSelectionNotice.value,
  );
  const agentErrorMessage = computed(
    () =>
      fieldErrors.value.agentId ||
      agentSelectionNotice.value ||
      selectedAgentSubmitDisabledReason.value,
  );

  const clearFormErrors = () => {
    submitError.value = "";
    fieldErrors.value = {};
    agentSelectionNotice.value = "";
  };

  const abortActiveCatalogRequest = () => {
    if (activeCatalogController) {
      activeCatalogController.abort();
      activeCatalogController = null;
    }
  };

  const setSelectedDatasetIds = (value: string[]) => {
    if (!form.value) {
      return;
    }

    const uniqueIds = Array.from(new Set(value));
    const nextIds = uniqueIds.slice(0, MAX_SUBMIT_DATASET_COUNT);
    form.value.selectedDatasetIds = nextIds;

    datasetSelectionNotice.value =
      uniqueIds.length > MAX_SUBMIT_DATASET_COUNT
        ? `最多只能选择 ${MAX_SUBMIT_DATASET_COUNT} 个数据集，超出的部分已忽略。`
        : "";

    if (nextIds.length > 0 && fieldErrors.value.selectedDatasetIds) {
      fieldErrors.value = {
        ...fieldErrors.value,
        selectedDatasetIds: undefined,
      };
    }
  };

  const applyDatasetQuerySelection = () => {
    if (!form.value || !datasetCatalogReady.value) {
      return;
    }

    const queryValue = route.query.datasetIds as
      | string
      | string[]
      | null
      | undefined;
    const querySignature = buildDatasetQuerySignature(queryValue);

    if (querySignature === appliedDatasetQuerySignature) {
      return;
    }

    appliedDatasetQuerySignature = querySignature;

    if (!querySignature) {
      return;
    }

    const resolvedDatasetIds = resolveDatasetIdsFromQuery(
      queryValue,
      validDatasetIds.value,
    );

    if (!resolvedDatasetIds.length) {
      datasetSelectionNotice.value = "链接中的数据集不可用，已忽略。";
      return;
    }

    setSelectedDatasetIds(resolvedDatasetIds);
  };

  const applyAgentQuerySelection = () => {
    if (!form.value || form.value.submitMethod !== "api") {
      return;
    }

    const queryValue =
      typeof route.query.agentId === "string" ? route.query.agentId.trim() : "";

    if (queryValue && queryValue !== appliedAgentQueryValue) {
      appliedAgentQueryValue = queryValue;
      const availableAgent = availableAgents.value.find(
        (item) => item.agentId === queryValue,
      );
      if (availableAgent) {
        form.value.agentId = availableAgent.agentId;
        agentSelectionNotice.value = "";
        return;
      }

      const blockedAgent = agents.value.find(
        (item) => item.agentId === queryValue,
      );
      agentSelectionNotice.value = blockedAgent
        ? getAgentSubmitDisabledReason(blockedAgent) || "链接中的 Agent 不可用，已忽略。"
        : "链接中的 Agent 不可用，已忽略。";
    }

    if (!form.value.agentId || !activeAgentIds.value.includes(form.value.agentId)) {
      form.value.agentId = activeAgentIds.value[0] ?? "";
    }
  };

  const buildPayloadSnapshot = (): SubmitPayloadSnapshot | null => {
    if (!form.value || !submitMeta.value) {
      return null;
    }

    const datasetIds = Array.from(
      new Set(form.value.selectedDatasetIds),
    ).sort();

    return {
      submitMethod: form.value.submitMethod,
      agentId: form.value.submitMethod === "api" ? form.value.agentId.trim() : "",
      parameters: {
        difficulty: normalizeDifficulty(
          form.value.parameters.difficulty,
          submitMeta.value.difficulty,
        ),
        timeoutMinutes: normalizeTimeoutMinutes(
          form.value.parameters.timeoutMinutes,
          submitMeta.value.timeoutMinutes,
        ),
        maxSteps: normalizeMaxSteps(
          form.value.parameters.maxSteps,
          submitMeta.value.maxSteps,
        ),
      },
      publicToLeaderboard: Boolean(form.value.publicToLeaderboard),
      datasetIds,
    };
  };

  const buildPayloadDigest = (): string => {
    const snapshot = buildPayloadSnapshot();
    return snapshot ? JSON.stringify(snapshot) : "";
  };

  const resolvePendingRequest = (
    payloadDigest: string,
  ): PendingSubmitRequest => {
    if (
      pendingRequest.value &&
      pendingRequest.value.payloadDigest === payloadDigest
    ) {
      return pendingRequest.value;
    }

    const nextPendingRequest: PendingSubmitRequest = {
      requestId: buildRequestId(),
      payloadDigest,
      createdAt: new Date().toISOString(),
    };
    submitDraftStore.setPendingRequest(nextPendingRequest);
    return nextPendingRequest;
  };

  const buildPayload = (mode: "preview" | "submit"): SubmitAgentPayload => {
    const snapshot = buildPayloadSnapshot();
    if (!snapshot) {
      throw new Error("提交表单尚未初始化完成。");
    }

    const payloadDigest = JSON.stringify(snapshot);
    const requestId =
      mode === "submit"
        ? resolvePendingRequest(payloadDigest).requestId
        : pendingRequest.value?.payloadDigest === payloadDigest
          ? pendingRequest.value.requestId
          : "preview_request_id";

    return {
      submitMethod: snapshot.submitMethod,
      agentId: snapshot.submitMethod === "api" ? snapshot.agentId : null,
      docker:
        snapshot.submitMethod === "docker"
          ? {
              imageUri: form.value?.docker.imageUri.trim() ?? "",
              command: form.value?.docker.command.trim() ?? "",
              env: {},
            }
          : null,
      parameters: snapshot.parameters,
      publicToLeaderboard: snapshot.publicToLeaderboard,
      selectedDatasetIds: snapshot.datasetIds,
      requestId,
    };
  };

  const buildConfirmMessage = (
    warnings: string[],
    payload: SubmitAgentPayload,
  ): string => {
    const header = [
      `智能体名称：${selectedAgent.value?.name ?? "未选择"}`,
      `提交方式：${payload.submitMethod.toUpperCase()}`,
      `数据集数量：${payload.selectedDatasetIds.length}`,
    ].join("\n");

    if (!warnings.length) {
      return `${header}\n\n检查已通过，确认后将创建评测任务。`;
    }

    return `${header}\n\n请先确认以下提示：\n- ${warnings.join(
      "\n- ",
    )}\n\n确认后将创建评测任务。`;
  };

  const syncCatalogSelection = () => {
    if (!datasetCatalog.catalog.value) {
      return;
    }

    submitDraftStore.syncWithCatalog(datasetCatalog.catalog.value.categories);
    applyDatasetQuerySelection();
  };

  const loadCatalog = async (force = false) => {
    abortActiveCatalogRequest();
    const controller = new AbortController();
    activeCatalogController = controller;

    try {
      await datasetCatalog.fetchCatalog({
        signal: controller.signal,
        force,
      });
      syncCatalogSelection();
    } catch (error) {
      if (isAbortLikeError(error)) {
        return;
      }

      throw error;
    } finally {
      if (activeCatalogController === controller) {
        activeCatalogController = null;
      }
    }
  };

  const initializePage = async () => {
    startLoading();
    clearFormErrors();
    datasetSelectionNotice.value = "";
    confirmDialogVisible.value = false;
    confirmedPayload.value = null;
    appliedDatasetQuerySignature = "";
    appliedAgentQueryValue = "";

    try {
      const [meta, agentList] = await Promise.all([
        getSubmitMeta(),
        getAgents({ includeArchived: false }),
      ]);
      agents.value = agentList;
      submitMeta.value = meta;
      submitDraftStore.applyMeta(meta);

      if (!form.value) {
        throw new Error("提交表单初始化失败。");
      }

      form.value.parameters.difficulty = normalizeDifficulty(
        form.value.parameters.difficulty,
        meta.difficulty,
      );
      form.value.parameters.timeoutMinutes = normalizeTimeoutMinutes(
        form.value.parameters.timeoutMinutes,
        meta.timeoutMinutes,
      );
      form.value.parameters.maxSteps = normalizeMaxSteps(
        form.value.parameters.maxSteps,
        meta.maxSteps,
      );
      setSelectedDatasetIds(form.value.selectedDatasetIds);

      await loadCatalog(true);
      applyAgentQuerySelection();
    } catch (error) {
      setError(error, "提交页初始化失败。");
    } finally {
      stopLoading();
    }
  };

  const selectAllDatasets = () => {
    setSelectedDatasetIds(validDatasetIds.value);
  };

  const clearAllDatasets = () => {
    setSelectedDatasetIds([]);
  };

  const toggleCategoryDatasets = (categoryId: string) => {
    if (!form.value) {
      return;
    }

    const category = enabledCategories.value.find(
      (item) => item.categoryId === categoryId,
    );
    if (!category) {
      return;
    }

    setSelectedDatasetIds(
      toggleCategoryDatasetsValue(
        category,
        form.value.selectedDatasetIds,
        MAX_SUBMIT_DATASET_COUNT,
      ),
    );
  };

  const toggleDataset = (datasetId: string) => {
    if (!form.value) {
      return;
    }

    setSelectedDatasetIds(
      toggleDatasetId(
        datasetId,
        form.value.selectedDatasetIds,
        MAX_SUBMIT_DATASET_COUNT,
      ),
    );
  };

  const toggleExpandedCategory = (categoryId: string) => {
    const nextExpanded = expandedCategoryIds.value.includes(categoryId)
      ? expandedCategoryIds.value.filter((item) => item !== categoryId)
      : [...expandedCategoryIds.value, categoryId];

    submitDraftStore.setExpandedCategoryIds(nextExpanded);
  };

  const retryDatasetCatalog = () => {
    void loadCatalog(true);
  };

  const resetDraft = () => {
    if (!submitMeta.value) {
      return;
    }

    submitDraftStore.resetDraft(
      submitMeta.value,
      datasetCatalog.catalog.value?.categories ?? [],
    );
    clearFormErrors();
    datasetSelectionNotice.value = "";
    confirmDialogVisible.value = false;
    confirmedPayload.value = null;
    appliedDatasetQuerySignature = "";
    appliedAgentQueryValue = "";
    applyDatasetQuerySelection();
    applyAgentQuerySelection();
  };

  const handleSubmit = async () => {
    if (!submitMeta.value || !form.value) {
      return;
    }

    clearFormErrors();

    if (form.value.submitMethod === "docker") {
      submitError.value = "Docker 提交功能正在升级中。";
      return;
    }

    if (datasetCatalogStatus.value === "empty") {
      submitError.value = "当前没有可用数据集，无法提交。";
      return;
    }

    if (!datasetCatalogReady.value) {
      submitError.value = "请等待数据集目录加载完成后再提交。";
      return;
    }

    startSubmitting();

    try {
      const payload = buildPayload("submit");
      const validation = validateSubmitPayload(
        payload,
        submitMeta.value,
        validDatasetIds.value,
        activeAgentIds.value,
      );

      if (!validation.valid) {
        fieldErrors.value = validation.fieldErrors;
        submitError.value = validation.errors[0] || "提交参数校验失败。";
        return;
      }

      const precheckResult = await precheckAgent(payload);
      confirmedPayload.value = payload;
      confirmDialogTitle.value = precheckResult.warnings.length
        ? "提交前确认"
        : "确认提交";
      confirmDialogMessage.value = buildConfirmMessage(
        precheckResult.warnings,
        payload,
      );
      confirmDialogVisible.value = true;
    } catch (error) {
      setSubmitError(error, "提交失败，请稍后重试。");
    } finally {
      stopSubmitting();
    }
  };

  const confirmSubmit = async () => {
    if (!confirmedPayload.value) {
      return;
    }

    startSubmitting();
    submitError.value = "";

    try {
      const submitResult = await submitAgent(confirmedPayload.value);
      confirmDialogVisible.value = false;
      submitDraftStore.clearDraftAfterSubmit();
      await router.push(
        RouteLocation.evaluationDetail(submitResult.evaluationId),
      );
    } catch (error) {
      setSubmitError(error, "提交失败，请稍后重试。");
    } finally {
      stopSubmitting();
    }
  };

  const canSubmit = computed(() => {
    if (!form.value || !submitMeta.value || !datasetCatalogReady.value) {
      return false;
    }

    if (form.value.submitMethod === "docker") {
      return false;
    }

    const payload = buildPayload("preview");
    return validateSubmitPayload(
      payload,
      submitMeta.value,
      validDatasetIds.value,
      activeAgentIds.value,
    ).valid;
  });

  watch(
    () => form.value?.parameters.difficulty,
    (value) => {
      if (!form.value || !submitMeta.value || typeof value !== "number") {
        return;
      }

      const normalized = normalizeDifficulty(
        value,
        submitMeta.value.difficulty,
      );
      if (normalized !== value) {
        form.value.parameters.difficulty = normalized;
      }
    },
  );

  watch(
    () => form.value?.parameters.timeoutMinutes,
    (value) => {
      if (!form.value || !submitMeta.value || typeof value !== "number") {
        return;
      }

      const normalized = normalizeTimeoutMinutes(
        value,
        submitMeta.value.timeoutMinutes,
      );
      if (normalized !== value) {
        form.value.parameters.timeoutMinutes = normalized;
      }
    },
  );

  watch(
    () => form.value?.parameters.maxSteps,
    (value) => {
      if (!form.value || !submitMeta.value || typeof value !== "number") {
        return;
      }

      const normalized = normalizeMaxSteps(value, submitMeta.value.maxSteps);
      if (normalized !== value) {
        form.value.parameters.maxSteps = normalized;
      }
    },
  );

  watch(
    () => form.value?.submitMethod,
    () => {
      applyAgentQuerySelection();
    },
  );

  watch(
    form,
    () => {
      const payloadDigest = buildPayloadDigest();
      if (
        pendingRequest.value &&
        payloadDigest &&
        pendingRequest.value.payloadDigest !== payloadDigest
      ) {
        submitDraftStore.setPendingRequest(null);
      }
    },
    {
      deep: true,
    },
  );

  watch(
    () => form.value?.selectedDatasetIds,
    (value) => {
      if (!value) {
        return;
      }

      if (value.length > 0 && fieldErrors.value.selectedDatasetIds) {
        fieldErrors.value = {
          ...fieldErrors.value,
          selectedDatasetIds: undefined,
        };
      }
    },
    {
      deep: true,
    },
  );

  watch(
    () => route.query.datasetIds,
    () => {
      if (!pageLoading.value) {
        applyDatasetQuerySelection();
      }
    },
  );

  watch(
    () => route.query.agentId,
    () => {
      if (!pageLoading.value) {
        applyAgentQuerySelection();
      }
    },
  );

  onMounted(async () => {
    await initializePage();
  });

  onBeforeUnmount(() => {
    abortActiveCatalogRequest();
  });

  return {
    form,
    submitMeta,
    pageLoading,
    pageError,
    submitting,
    submitError,
    fieldErrors,
    agents,
    availableAgents,
    selectedAgent,
    selectedAgentSubmitDisabledReason,
    agentErrorMessage,
    expandedCategoryIds,
    datasetCatalogStatus,
    datasetCatalogErrorMessage,
    enabledCategories,
    selectedCategoryCount,
    selectedDatasetNames,
    selectionErrorMessage,
    confirmDialogVisible,
    confirmDialogTitle,
    confirmDialogMessage,
    canSubmit,
    setSubmitMethod: submitDraftStore.setSubmitMethod,
    setAgentId: submitDraftStore.setAgentId,
    initializePage,
    handleSubmit,
    confirmSubmit,
    selectAllDatasets,
    clearAllDatasets,
    toggleCategoryDatasets,
    toggleDataset,
    toggleExpandedCategory,
    retryDatasetCatalog,
    resetDraft,
  };
};
