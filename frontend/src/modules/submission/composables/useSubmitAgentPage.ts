import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
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
import {
  buildDatasetQuerySignature,
  resolveDatasetIdsFromQuery,
} from "@/modules/submission/lib/submit-query-utils";
import {
  buildSubmitConfirmMessage,
  buildSubmitRequestId,
  isSubmitAbortError,
} from "@/modules/submission/model/submit-actions";
import {
  normalizeSubmitDraftParameters,
  shouldClearPendingSubmitRequest,
} from "@/modules/submission/model/submit-draft-sync";
import {
  buildSubmitPayloadDigest as stringifySubmitPayloadSnapshot,
  buildSubmitPayloadFromSnapshot,
  buildSubmitPayloadSnapshot,
} from "@/modules/submission/model/submit-payload-snapshot";
import type { SubmitPayloadSnapshot } from "@/modules/submission/model/submit-payload-snapshot";
import type {
  PendingSubmitRequest,
  SubmitAgentPayload,
  SubmitFieldErrors,
  SubmitMetaResponse,
} from "@/shared/types/agent-types";
import type { AgentListItem } from "@/shared/types/agent-registry-types";
import { useAsyncState } from "@/shared/composables/useAsyncState";

export const useSubmitAgentPage = () => {
  const route = useRoute();
  const router = useRouter();
  const { t } = useI18n();
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
  const confirmDialogTitle = ref(t("submission.confirm.submitTitle"));
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

    return (
      availableAgents.value.find((agent) => agent.agentId === agentId) ?? null
    );
  });
  const selectedAgentSubmitDisabledReason = computed(() =>
    selectedAgent.value
      ? getAgentSubmitDisabledReason(selectedAgent.value, t)
      : "",
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
        ? t("submission.validation.selectedDatasetLimitNotice", {
            count: MAX_SUBMIT_DATASET_COUNT,
          })
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
      datasetSelectionNotice.value = t("submission.errors.datasetUnavailable");
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
        ? getAgentSubmitDisabledReason(blockedAgent, t) ||
          t("submission.errors.invalidAgentLink")
        : t("submission.errors.invalidAgentLink");
    }

    if (
      !form.value.agentId ||
      !activeAgentIds.value.includes(form.value.agentId)
    ) {
      form.value.agentId = activeAgentIds.value[0] ?? "";
    }
  };

  const buildPayloadSnapshot = (): SubmitPayloadSnapshot | null => {
    return buildSubmitPayloadSnapshot(form.value, submitMeta.value);
  };

  const buildPayloadDigest = (): string => {
    const snapshot = buildPayloadSnapshot();
    return stringifySubmitPayloadSnapshot(snapshot);
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
      requestId: buildSubmitRequestId(),
      payloadDigest,
      createdAt: new Date().toISOString(),
    };
    submitDraftStore.setPendingRequest(nextPendingRequest);
    return nextPendingRequest;
  };

  const buildPayload = (mode: "preview" | "submit"): SubmitAgentPayload => {
    const snapshot = buildPayloadSnapshot();
    if (!snapshot) {
      throw new Error(t("submission.errors.submitFormNotReady"));
    }

    const payloadDigest = JSON.stringify(snapshot);
    const requestId =
      mode === "submit"
        ? resolvePendingRequest(payloadDigest).requestId
        : pendingRequest.value?.payloadDigest === payloadDigest
          ? pendingRequest.value.requestId
          : "preview_request_id";

    if (!form.value) {
      throw new Error(t("submission.errors.submitFormNotReady"));
    }

    return buildSubmitPayloadFromSnapshot(snapshot, form.value, requestId);
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
      if (isSubmitAbortError(error)) {
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
        throw new Error(t("submission.errors.submitFormInitFailed"));
      }

      form.value.parameters = normalizeSubmitDraftParameters(form.value, meta);
      setSelectedDatasetIds(form.value.selectedDatasetIds);

      await loadCatalog(true);
      applyAgentQuerySelection();
    } catch (error) {
      setError(error, t("submission.errors.submitInitFailed"));
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
      submitError.value = t("submission.errors.dockerUpgrade");
      return;
    }

    if (datasetCatalogStatus.value === "empty") {
      submitError.value = t("submission.errors.noDataset");
      return;
    }

    if (!datasetCatalogReady.value) {
      submitError.value = t("submission.errors.datasetCatalogPending");
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
        t,
      );

      if (!validation.valid) {
        fieldErrors.value = validation.fieldErrors;
        submitError.value =
          validation.errors[0] || t("submission.errors.validationFailed");
        return;
      }

      const precheckResult = await precheckAgent(payload);
      confirmedPayload.value = payload;
      confirmDialogTitle.value = precheckResult.warnings.length
        ? t("submission.confirm.precheckTitle")
        : t("submission.confirm.submitTitle");
      confirmDialogMessage.value = buildSubmitConfirmMessage(
        selectedAgent.value?.name ?? "",
        precheckResult.warnings,
        payload,
        t,
      );
      confirmDialogVisible.value = true;
    } catch (error) {
      setSubmitError(error, t("submission.errors.submitFailed"));
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
      setSubmitError(error, t("submission.errors.submitFailed"));
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
      t,
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
        shouldClearPendingSubmitRequest(pendingRequest.value, payloadDigest)
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
