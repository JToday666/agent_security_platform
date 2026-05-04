import { computed, onMounted, ref, watch } from "vue";
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
import { shouldPollEvaluation } from "@/modules/evaluation/lib/evaluation-status";
import type {
  EvaluationAction,
  EvaluationDetail,
  EvaluationReportPayload,
} from "@/shared/types/agent-types";
import { useAsyncState } from "@/shared/composables/useAsyncState";
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
  const evaluationId = computed(() => String(route.params.evaluationId ?? ""));
  const report = ref<EvaluationReportPayload | null>(null);
  const reportLoading = ref(false);
  const reportError = ref("");
  const reportUnavailableFor = ref("");
  const downloadLoading = ref(false);
  const downloadError = ref("");

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
    if (pendingAction.value === "pause") return "暂停任务";
    if (pendingAction.value === "terminate") return "终止任务";
    if (pendingAction.value === "cancel") return "取消任务";
    return "";
  });

  const actionDialogMessage = computed(() => {
    if (pendingAction.value === "pause")
      return "暂停会在当前数据集执行完成后生效，每个任务最多只允许暂停一次。";
    if (pendingAction.value === "terminate")
      return "终止会在当前数据集执行完成后结束剩余队列，并生成最终报告。";
    if (pendingAction.value === "cancel")
      return "取消会立即中断当前任务，并且不会生成最终报告。";
    return "";
  });

  const actionDialogConfirmText = computed(() => {
    if (pendingAction.value === "pause") return "确认暂停";
    if (pendingAction.value === "terminate") return "确认终止";
    return "确认取消";
  });

  const actionDialogDanger = computed(() => pendingAction.value === "cancel");

  const reportStateText = computed(() => {
    if (reportUnavailableFor.value === evaluationId.value) {
      return getReportUnavailableMessage();
    }

    if (report.value) {
      return "报告已生成，可查看摘要和详细指标。";
    }

    if (!detail.value) {
      return "正在同步报告状态。";
    }

    if (
      detail.value.status === "canceled" ||
      detail.value.status === "failed"
    ) {
      return "当前任务未生成最终报告。";
    }

    if (
      detail.value.status === "completed" ||
      detail.value.status === "terminated"
    ) {
      return "任务已结束，但当前未返回报告内容。";
    }

    return "报告尚未生成，请等待任务继续执行。";
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
        loadError instanceof Error ? loadError.message : "评测报告加载失败。";
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

    if (report.value?.evaluationId === detail.value.evaluationId) {
      return;
    }

    if (reportUnavailableFor.value === detail.value.evaluationId) {
      return;
    }

    void loadReport();
  };

  const doLoadDetail = async () => {
    try {
      detail.value = await getEvaluationDetail(evaluationId.value);
      error.value = "";
      syncReport();
      syncPolling();
    } catch (loadError) {
      setError(loadError, "评测详情加载失败。");
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

  const poll = usePolling(doLoadDetail, () => {
    return Boolean(detail.value && shouldPollEvaluation(detail.value.status));
  });

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
    downloadLoading.value = true;
    downloadError.value = "";

    try {
      const { blob, fileName } = await downloadEvaluationSampleDetails(
        evaluationId.value,
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
      downloadError.value = "样本明细下载失败，请稍后重试。";
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
        actionErr instanceof Error ? actionErr.message : "任务操作失败。";
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
