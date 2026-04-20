import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { RouteLocation } from "@/app/router/route-names";
import {
  getEvaluationDetail,
  postEvaluationAction,
} from "@/modules/evaluation/api/evaluation-api";
import { shouldPollEvaluation } from "@/modules/evaluation/lib/evaluation-status";
import type {
  EvaluationAction,
  EvaluationDetail,
} from "@/shared/types/agent-types";

const POLL_INTERVAL_MS = 10 * 60 * 1000;

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

  const detail = ref<EvaluationDetail | null>(null);
  const loading = ref(true);
  const error = ref("");
  const actionLoading = ref(false);
  const pendingAction = ref<EvaluationAction | null>(null);
  const actionDialogVisible = ref(false);
  const actionDialogTitle = ref("");
  const actionDialogMessage = ref("");
  const actionDialogConfirmText = ref("确认");
  const actionDialogDanger = ref(false);

  let pollTimer: number | null = null;

  const reportStateText = computed(() => {
    if (detail.value?.report) {
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

  const clearPolling = () => {
    if (pollTimer !== null) {
      window.clearInterval(pollTimer);
      pollTimer = null;
    }
  };

  const syncPolling = () => {
    clearPolling();

    if (!detail.value || !shouldPollEvaluation(detail.value.status)) {
      return;
    }

    pollTimer = window.setInterval(() => {
      void loadDetail(true);
    }, POLL_INTERVAL_MS);
  };

  const loadDetail = async (silent = false) => {
    if (!silent || !detail.value) {
      loading.value = true;
    }

    if (!silent) {
      error.value = "";
    }

    try {
      detail.value = await getEvaluationDetail(evaluationId.value);
      error.value = "";
      syncPolling();
    } catch (loadError) {
      error.value =
        loadError instanceof Error ? loadError.message : "评测详情加载失败。";
      clearPolling();
    } finally {
      loading.value = false;
    }
  };

  const applyDetail = (nextDetail: EvaluationDetail) => {
    detail.value = nextDetail;
    error.value = "";
    syncPolling();
  };

  const goBack = () => {
    void router.push(RouteLocation.userCenter);
  };

  const openActionDialog = (action: EvaluationAction) => {
    pendingAction.value = action;
    actionDialogDanger.value = action === "cancel";
    actionDialogConfirmText.value =
      action === "pause"
        ? "确认暂停"
        : action === "terminate"
          ? "确认终止"
          : "确认取消";

    if (action === "pause") {
      actionDialogTitle.value = "暂停任务";
      actionDialogMessage.value =
        "暂停会在当前数据集执行完成后生效，每个任务最多只允许暂停一次。";
    } else if (action === "terminate") {
      actionDialogTitle.value = "终止任务";
      actionDialogMessage.value =
        "终止会在当前数据集执行完成后结束剩余队列，并生成最终报告。";
    } else {
      actionDialogTitle.value = "取消任务";
      actionDialogMessage.value =
        "取消会立即中断当前任务，并且不会生成最终报告。";
    }

    actionDialogVisible.value = true;
  };

  const runAction = async (action: EvaluationAction) => {
    actionLoading.value = true;
    error.value = "";

    try {
      const nextDetail = await postEvaluationAction(evaluationId.value, action);
      applyDetail(nextDetail);
    } catch (actionError) {
      const code = getErrorCode(actionError);
      const message =
        actionError instanceof Error ? actionError.message : "任务操作失败。";
      error.value = message;

      if (code === 40901 || code === 40902) {
        await loadDetail(true);
        error.value = message;
      }
    } finally {
      actionLoading.value = false;
    }
  };

  const confirmAction = async () => {
    if (!pendingAction.value) {
      return;
    }

    const action = pendingAction.value;
    await runAction(action);
    pendingAction.value = null;
    actionDialogVisible.value = false;
  };

  watch(evaluationId, async () => {
    clearPolling();
    detail.value = null;
    pendingAction.value = null;
    actionDialogVisible.value = false;
    await loadDetail();
  });

  onMounted(async () => {
    await loadDetail();
  });

  onBeforeUnmount(() => {
    clearPolling();
  });

  return {
    detail,
    loading,
    error,
    reportStateText,
    actionLoading,
    actionDialogVisible,
    actionDialogTitle,
    actionDialogMessage,
    actionDialogConfirmText,
    actionDialogDanger,
    loadDetail,
    goBack,
    openActionDialog,
    runAction,
    confirmAction,
  };
};
