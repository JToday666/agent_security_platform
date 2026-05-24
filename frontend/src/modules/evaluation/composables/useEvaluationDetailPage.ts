import { computed, onMounted, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { useRoute, useRouter } from "vue-router";
import { RouteLocation } from "@/app/router/route-names";
import {
  downloadEvaluationSampleDetails,
  getEvaluationDetail,
  getEvaluationReport,
  postEvaluationAction,
} from "@/modules/evaluation/api/evaluation-api";
import {
  getReportUnavailableMessage,
  isReportEndpointUnavailableError,
} from "@/modules/evaluation/lib/evaluation-report-state";
import {
  EVALUATION_POLL_INTERVAL_MS,
  EVALUATION_TERMINAL_REPORT_POLL_WINDOW_MS,
  shouldExpectEvaluationReport,
  shouldPollEvaluation,
} from "@/modules/evaluation/lib/evaluation-status";
import type {
  EvaluationAction,
  EvaluationDetail,
  EvaluationReportPayload,
} from "@/shared/types/agent-types";
import {
  getErrorMessage,
  useAsyncState,
} from "@/shared/composables/useAsyncState";
import { usePolling } from "@/shared/composables/usePolling";

const getErrorCode = (value: unknown): number | null => {
  if (!value || typeof value !== "object" || !("code" in value)) {
    return null;
  }

  const code = Number((value as { code?: unknown }).code);
  return Number.isFinite(code) ? code : null;
};

export const useEvaluationDetailPage = () => {
  const route = useRoute();
  const router = useRouter();
  const { t } = useI18n();
  const evaluationId = computed(() => String(route.params.evaluationId ?? ""));
  const report = ref<EvaluationReportPayload | null>(null);
  const reportLoading = ref(false);
  const reportError = ref("");
  const reportUnavailableFor = ref("");
  const downloadLoading = ref(false);
  const downloadError = ref("");
  const terminalReportPollingStartedAt = ref<number | null>(null);

  const {
    data: detail,
    loading,
    error,
    startLoading,
    stopLoading,
    setError,
  } = useAsyncState<EvaluationDetail>();

  const {
    data: pendingAction,
    loading: actionLoading,
    startLoading: startActionLoading,
    stopLoading: stopActionLoading,
  } = useAsyncState<EvaluationAction>();

  const actionDialogVisible = computed({
    get: () => pendingAction.value !== null,
    set: (v) => {
      if (!v) pendingAction.value = null;
    },
  });

  const actionDialogTitle = computed(() => {
    if (pendingAction.value === "pause")
      return t("evaluation.dialogs.pauseTitle");
    if (pendingAction.value === "terminate")
      return t("evaluation.dialogs.terminateTitle");
    if (pendingAction.value === "cancel")
      return t("evaluation.dialogs.cancelTitle");
    return "";
  });

  const actionDialogMessage = computed(() => {
    if (pendingAction.value === "pause")
      return t("evaluation.dialogs.pauseMessage");
    if (pendingAction.value === "terminate")
      return t("evaluation.dialogs.terminateMessage");
    if (pendingAction.value === "cancel")
      return t("evaluation.dialogs.cancelMessage");
    return "";
  });

  const actionDialogConfirmText = computed(() => {
    if (pendingAction.value === "pause")
      return t("evaluation.actions.confirmPause");
    if (pendingAction.value === "terminate")
      return t("evaluation.actions.confirmTerminate");
    return t("evaluation.actions.confirmCancel");
  });

  const actionDialogDanger = computed(() => pendingAction.value === "cancel");

  const reportStateText = computed(() => {
    if (reportUnavailableFor.value === evaluationId.value) {
      return getReportUnavailableMessage(t);
    }

    if (report.value) {
      return t("evaluation.report.generated");
    }

    if (!detail.value) {
      return t("evaluation.report.stateSync");
    }

    if (
      detail.value.status === "canceled" ||
      detail.value.status === "failed"
    ) {
      return t("evaluation.report.missingFinal");
    }

    if (
      detail.value.status === "completed" ||
      detail.value.status === "terminated"
    ) {
      return t("evaluation.report.missingReturned");
    }

    return t("evaluation.report.pending");
  });

  const loadReport = async () => {
    if (!detail.value?.finalReportAvailable) {
      report.value = null;
      reportError.value = "";
      return;
    }

    reportLoading.value = true;
    reportError.value = "";
    reportUnavailableFor.value = "";

    try {
      report.value = await getEvaluationReport(evaluationId.value);
    } catch (loadError) {
      report.value = null;
      if (isReportEndpointUnavailableError(loadError)) {
        reportUnavailableFor.value = evaluationId.value;
        reportError.value = "";
        return;
      }

      reportError.value =
        getErrorMessage(loadError, t("evaluation.api.reportLoadFailed"));
    } finally {
      reportLoading.value = false;
    }
  };

  const syncReport = () => {
    if (!detail.value?.finalReportAvailable) {
      report.value = null;
      reportError.value = "";
      return;
    }

    if (
      reportLoading.value ||
      report.value?.evaluationId === detail.value.evaluationId
    ) {
      return;
    }

    void loadReport();
  };

  const syncTerminalReportPollingWindow = () => {
    if (!detail.value) {
      terminalReportPollingStartedAt.value = null;
      return;
    }

    const shouldPollForReport =
      shouldExpectEvaluationReport(detail.value.status) &&
      !report.value &&
      !reportError.value;

    if (!shouldPollForReport) {
      terminalReportPollingStartedAt.value = null;
      return;
    }

    terminalReportPollingStartedAt.value ??= Date.now();
  };

  const shouldContinueTerminalReportPolling = () => {
    syncTerminalReportPollingWindow();
    if (terminalReportPollingStartedAt.value === null) {
      return false;
    }

    return (
      Date.now() - terminalReportPollingStartedAt.value <=
      EVALUATION_TERMINAL_REPORT_POLL_WINDOW_MS
    );
  };

  const doLoadDetail = async () => {
    try {
      detail.value = await getEvaluationDetail(evaluationId.value);
      error.value = "";
      syncReport();
      syncTerminalReportPollingWindow();
      syncPolling();
    } catch (loadError) {
      setError(loadError, t("evaluation.api.detailLoadFailed"));
      poll.stop();
    }
  };

  const loadDetail = async (silent = false) => {
    if (!silent || !detail.value) {
      startLoading();
    }

    if (!silent) {
      error.value = "";
    }

    await doLoadDetail();

    stopLoading();
  };

  const poll = usePolling(
    doLoadDetail,
    () =>
      Boolean(
        detail.value &&
          (shouldPollEvaluation(detail.value.status) ||
            shouldContinueTerminalReportPolling()),
      ),
    EVALUATION_POLL_INTERVAL_MS,
  );

  const syncPolling = () => {
    poll.start();
  };

  const applyDetail = (nextDetail: EvaluationDetail) => {
    detail.value = nextDetail;
    error.value = "";
    syncReport();
    syncPolling();
  };

  const goBack = () => {
    void router.push(RouteLocation.userCenter);
  };

  const downloadSampleDetails = async () => {
    const sampleDetailsUrl = detail.value?.downloads.sampleDetailsUrl;
    if (!sampleDetailsUrl) {
      downloadError.value = t("evaluation.api.sampleDownloadFailed");
      return;
    }

    downloadLoading.value = true;
    downloadError.value = "";

    try {
      const { blob, fileName } = await downloadEvaluationSampleDetails(
        sampleDetailsUrl,
      );
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = fileName || `${evaluationId.value}-samples.zip`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch {
      downloadError.value = t("evaluation.api.sampleDownloadFailed");
    } finally {
      downloadLoading.value = false;
    }
  };

  const openActionDialog = (action: EvaluationAction) => {
    pendingAction.value = action;
  };

  const runAction = async (action: EvaluationAction) => {
    startActionLoading();

    try {
      const nextDetail = await postEvaluationAction(evaluationId.value, action);
      applyDetail(nextDetail);
    } catch (actionErr) {
      const code = getErrorCode(actionErr);
      const message =
        getErrorMessage(actionErr, t("evaluation.api.actionFailed"));
      error.value = message;

      if (code === 40901 || code === 40902) {
        await loadDetail(true);
        error.value = message;
      }
    } finally {
      stopActionLoading();
    }
  };

  const confirmAction = async () => {
    if (!pendingAction.value) {
      return;
    }

    const action = pendingAction.value;
    await runAction(action);
    pendingAction.value = null;
  };

  watch(evaluationId, async () => {
    poll.stop();
    detail.value = null;
    report.value = null;
    reportError.value = "";
    reportUnavailableFor.value = "";
    terminalReportPollingStartedAt.value = null;
    downloadError.value = "";
    pendingAction.value = null;
    await loadDetail();
  });

  onMounted(async () => {
    await loadDetail();
  });

  return {
    detail,
    loading,
    error,
    report,
    reportLoading,
    reportError,
    reportStateText,
    downloadLoading,
    downloadError,
    actionLoading,
    actionDialogVisible,
    actionDialogTitle,
    actionDialogMessage,
    actionDialogConfirmText,
    actionDialogDanger,
    loadDetail,
    loadReport,
    goBack,
    downloadSampleDetails,
    openActionDialog,
    runAction,
    confirmAction,
  };
};
