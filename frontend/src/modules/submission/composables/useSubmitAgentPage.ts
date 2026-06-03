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
import { useSubmitDraftStore } from "@/modules/submission/stores/submitDraftStore";
import { useSubmitAttackScenarioCatalog } from "./useSubmitAttackScenarioCatalog";
import {
  MAX_SUBMIT_EVALUATION_ITEM_COUNT,
  normalizeDifficulty,
  normalizeMaxSteps,
  normalizeTimeoutMinutes,
  validateSubmitPayload,
} from "@/modules/submission/model/parameter-validator";
import { filterAvailableSubmitAgents } from "@/modules/submission/model/submit-agent-options";
import {
  buildEvaluationItemQuerySignature,
  resolveEvaluationItemIdsFromQuery,
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
  const attackScenarioCatalog = useSubmitAttackScenarioCatalog();
  const attackScenarioCatalogStatus = attackScenarioCatalog.status;
  const attackScenarioCatalogErrorMessage = attackScenarioCatalog.errorMessage;

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
  const evaluationItemSelectionNotice = ref("");
  const agentSelectionNotice = ref("");
  const confirmDialogVisible = ref(false);
  const confirmDialogTitle = ref(t("submission.confirm.submitTitle"));
  const confirmDialogMessage = ref("");
  const confirmedPayload = ref<SubmitAgentPayload | null>(null);

  let activeCatalogController: AbortController | null = null;
  let appliedEvaluationItemQuerySignature = "";
  let appliedAgentQueryValue = "";

  const enabledAttackScenarios = computed(
    () => attackScenarioCatalog.enabledAttackScenarios.value,
  );
  const selectedAttackScenario = computed(() =>
    enabledAttackScenarios.value.find(
      (scenario) =>
        scenario.attackScenarioId === form.value?.selectedAttackScenarioId,
    ) ?? null,
  );
  const enabledCategories = computed(
    () => selectedAttackScenario.value?.riskDomains ?? [],
  );
  const validEvaluationItemIds = computed(() =>
    enabledCategories.value.flatMap((riskDomain) =>
      riskDomain.evaluationItems.map((item) => item.evaluationItemId),
    ),
  );
  const attackScenarioCatalogReady = computed(
    () => attackScenarioCatalogStatus.value === "ready",
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
        category.evaluationItems.some((item) =>
          form.value?.selectedEvaluationItemIds.includes(
            item.evaluationItemId,
          ),
        ),
      ).length,
  );
  const selectedEvaluationItemNames = computed(() => {
    if (!form.value) {
      return [];
    }

    const nameById = new Map(
      enabledCategories.value.flatMap((category) =>
        category.evaluationItems.map(
          (item) => [item.evaluationItemId, item.name] as const,
        ),
      ),
    );

    return form.value.selectedEvaluationItemIds
      .map((evaluationItemId) => nameById.get(evaluationItemId))
      .filter((name): name is string => Boolean(name));
  });
  const selectionErrorMessage = computed(
    () =>
      fieldErrors.value.selectedEvaluationItemIds ||
      evaluationItemSelectionNotice.value,
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

  const setSelectedEvaluationItemIds = (value: string[]) => {
    if (!form.value) {
      return;
    }

    const uniqueIds = Array.from(new Set(value));
    const nextIds = uniqueIds.slice(0, MAX_SUBMIT_EVALUATION_ITEM_COUNT);
    form.value.selectedEvaluationItemIds = nextIds;

    evaluationItemSelectionNotice.value =
      uniqueIds.length > MAX_SUBMIT_EVALUATION_ITEM_COUNT
        ? t("submission.validation.selectedEvaluationItemLimitNotice", {
            count: MAX_SUBMIT_EVALUATION_ITEM_COUNT,
          })
        : "";

    if (nextIds.length > 0 && fieldErrors.value.selectedEvaluationItemIds) {
      fieldErrors.value = {
        ...fieldErrors.value,
        selectedEvaluationItemIds: undefined,
      };
    }
  };

  const applyEvaluationItemQuerySelection = () => {
    if (!form.value || !attackScenarioCatalogReady.value) {
      return;
    }

    const scenarioQueryValue =
      typeof route.query.attackScenarioId === "string"
        ? route.query.attackScenarioId.trim()
        : "";
    if (scenarioQueryValue) {
      submitDraftStore.setAttackScenarioId(scenarioQueryValue);
    }

    const queryValue = route.query.evaluationItemIds as
      | string
      | string[]
      | null
      | undefined;
    const querySignature = buildEvaluationItemQuerySignature(queryValue);

    if (querySignature === appliedEvaluationItemQuerySignature) {
      return;
    }

    appliedEvaluationItemQuerySignature = querySignature;

    if (!querySignature) {
      return;
    }

    const resolvedEvaluationItemIds = resolveEvaluationItemIdsFromQuery(
      queryValue,
      validEvaluationItemIds.value,
    );

    if (!resolvedEvaluationItemIds.length) {
      evaluationItemSelectionNotice.value = t(
        "submission.errors.evaluationItemUnavailable",
      );
      return;
    }

    setSelectedEvaluationItemIds(resolvedEvaluationItemIds);
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
    if (!attackScenarioCatalog.catalog.value) {
      return;
    }

    submitDraftStore.syncWithCatalog(attackScenarioCatalog.catalog.value);
    applyEvaluationItemQuerySelection();
  };

  const loadCatalog = async (force = false) => {
    abortActiveCatalogRequest();
    const controller = new AbortController();
    activeCatalogController = controller;

    try {
      await attackScenarioCatalog.fetchCatalog({
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
    evaluationItemSelectionNotice.value = "";
    confirmDialogVisible.value = false;
    confirmedPayload.value = null;
    appliedEvaluationItemQuerySignature = "";
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
      setSelectedEvaluationItemIds(form.value.selectedEvaluationItemIds);

      await loadCatalog(true);
      applyAgentQuerySelection();
    } catch (error) {
      setError(error, t("submission.errors.submitInitFailed"));
    } finally {
      stopLoading();
    }
  };

  const selectAllEvaluationItems = () => {
    setSelectedEvaluationItemIds(validEvaluationItemIds.value);
  };

  const clearAllEvaluationItems = () => {
    setSelectedEvaluationItemIds([]);
  };

  const toggleRiskDomainEvaluationItems = (categoryId: string) => {
    if (!form.value) {
      return;
    }

    const category = enabledCategories.value.find(
      (item) => item.riskDomainId === categoryId,
    );
    if (!category) {
      return;
    }

    const itemIds = category.evaluationItems.map((item) => item.evaluationItemId);
    const fullySelected = itemIds.every((item) =>
      form.value?.selectedEvaluationItemIds.includes(item),
    );
    setSelectedEvaluationItemIds(
      fullySelected
        ? form.value.selectedEvaluationItemIds.filter(
            (item) => !itemIds.includes(item),
          )
        : Array.from(
            new Set([...form.value.selectedEvaluationItemIds, ...itemIds]),
          ).slice(0, MAX_SUBMIT_EVALUATION_ITEM_COUNT),
    );
  };

  const toggleEvaluationItem = (evaluationItemId: string) => {
    if (!form.value) {
      return;
    }

    setSelectedEvaluationItemIds(
      form.value.selectedEvaluationItemIds.includes(evaluationItemId)
        ? form.value.selectedEvaluationItemIds.filter(
            (item) => item !== evaluationItemId,
          )
        : [...form.value.selectedEvaluationItemIds, evaluationItemId].slice(
            0,
            MAX_SUBMIT_EVALUATION_ITEM_COUNT,
          ),
    );
  };

  const toggleExpandedCategory = (categoryId: string) => {
    const nextExpanded = expandedCategoryIds.value.includes(categoryId)
      ? expandedCategoryIds.value.filter((item) => item !== categoryId)
      : [...expandedCategoryIds.value, categoryId];

    submitDraftStore.setExpandedCategoryIds(nextExpanded);
  };

  const setAttackScenarioId = (attackScenarioId: string) => {
    submitDraftStore.setAttackScenarioId(attackScenarioId);
    evaluationItemSelectionNotice.value = "";
    fieldErrors.value = {
      ...fieldErrors.value,
      selectedEvaluationItemIds: undefined,
    };
    appliedEvaluationItemQuerySignature = "";
  };

  const retryAttackScenarioCatalog = () => {
    void loadCatalog(true);
  };

  const resetDraft = () => {
    if (!submitMeta.value) {
      return;
    }

    submitDraftStore.resetDraft(
      submitMeta.value,
      attackScenarioCatalog.catalog.value,
    );
    clearFormErrors();
    evaluationItemSelectionNotice.value = "";
    confirmDialogVisible.value = false;
    confirmedPayload.value = null;
    appliedEvaluationItemQuerySignature = "";
    appliedAgentQueryValue = "";
    applyEvaluationItemQuerySelection();
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

    if (attackScenarioCatalogStatus.value === "empty") {
      submitError.value = t("submission.errors.noEvaluationItems");
      return;
    }

    if (!attackScenarioCatalogReady.value) {
      submitError.value = t("submission.errors.catalogPending");
      return;
    }

    startSubmitting();

    try {
      const payload = buildPayload("submit");
      const validation = validateSubmitPayload(
        payload,
        submitMeta.value,
        validEvaluationItemIds.value,
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
    if (!form.value || !submitMeta.value || !attackScenarioCatalogReady.value) {
      return false;
    }

    if (form.value.submitMethod === "docker") {
      return false;
    }

    const payload = buildPayload("preview");
    return validateSubmitPayload(
      payload,
      submitMeta.value,
      validEvaluationItemIds.value,
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
    () => form.value?.selectedEvaluationItemIds,
    (value) => {
      if (!value) {
        return;
      }

      if (value.length > 0 && fieldErrors.value.selectedEvaluationItemIds) {
        fieldErrors.value = {
          ...fieldErrors.value,
          selectedEvaluationItemIds: undefined,
        };
      }
    },
    {
      deep: true,
    },
  );

  watch(
    () => [route.query.attackScenarioId, route.query.evaluationItemIds],
    () => {
      if (!pageLoading.value) {
        applyEvaluationItemQuerySelection();
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
    attackScenarioCatalogStatus,
    attackScenarioCatalogErrorMessage,
    enabledAttackScenarios,
    selectedAttackScenario,
    enabledCategories,
    selectedCategoryCount,
    selectedEvaluationItemNames,
    selectionErrorMessage,
    confirmDialogVisible,
    confirmDialogTitle,
    confirmDialogMessage,
    canSubmit,
    setSubmitMethod: submitDraftStore.setSubmitMethod,
    setAgentId: submitDraftStore.setAgentId,
    setAttackScenarioId,
    initializePage,
    handleSubmit,
    confirmSubmit,
    selectAllEvaluationItems,
    clearAllEvaluationItems,
    toggleRiskDomainEvaluationItems,
    toggleEvaluationItem,
    toggleExpandedCategory,
    retryAttackScenarioCatalog,
    resetDraft,
  };
};
