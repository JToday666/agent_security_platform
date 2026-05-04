import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { RouteLocation } from "@/app/router/route-names";
import {
  archiveAgent,
  getAgentDetail,
  verifyAgent,
} from "@/modules/agent/api/agent-api";
import {
  buildAgentAuthItems,
  buildAgentConnectionItems,
  buildAgentCustomRequestBodyJson,
  buildAgentInputMappingItems,
  buildAgentOutputMappingItems,
  buildAgentStatusItems,
  buildAgentSummaryItems,
  buildAgentVerificationMessageGroups,
  buildAgentVerificationStatItems,
  formatAgentVerificationLabel,
  getAgentVerificationResultIcon,
  getAgentVerificationResultLabel,
} from "@/modules/agent/lib/agent-detail-view";
import type { AgentDetail } from "@/shared/types/agent-registry-types";

export const useAgentDetailPage = () => {
  const route = useRoute();
  const router = useRouter();

  const detail = ref<AgentDetail | null>(null);
  const loading = ref(true);
  const error = ref("");
  const actionError = ref("");
  const busyAction = ref<"verify" | "archive" | "">("");
  const archiveDialogVisible = ref(false);

  const agentId = computed(() =>
    typeof route.params.agentId === "string" ? route.params.agentId : "",
  );
  const busy = computed(() => Boolean(busyAction.value));
  const verificationLabel = computed(() =>
    detail.value ? formatAgentVerificationLabel(detail.value) : "未验证",
  );
  const verificationResultLabel = computed(() =>
    detail.value ? getAgentVerificationResultLabel(detail.value) : "",
  );
  const verificationResultIcon = computed(() =>
    detail.value ? getAgentVerificationResultIcon(detail.value) : "",
  );
  const summaryItems = computed(() =>
    detail.value ? buildAgentSummaryItems(detail.value) : [],
  );
  const connectionItems = computed(() =>
    detail.value ? buildAgentConnectionItems(detail.value) : [],
  );
  const authItems = computed(() =>
    detail.value ? buildAgentAuthItems(detail.value) : [],
  );
  const inputMappingItems = computed(() =>
    detail.value
      ? buildAgentInputMappingItems(detail.value.platformInputMapping)
      : [],
  );
  const outputMappingItems = computed(() =>
    detail.value
      ? buildAgentOutputMappingItems(detail.value.platformOutputMapping)
      : [],
  );
  const statusItems = computed(() =>
    detail.value ? buildAgentStatusItems(detail.value) : [],
  );
  const customRequestBodyJson = computed(() =>
    detail.value ? buildAgentCustomRequestBodyJson(detail.value) : "{}",
  );
  const verificationStatItems = computed(() =>
    detail.value ? buildAgentVerificationStatItems(detail.value) : [],
  );
  const verificationMessageGroups = computed(() =>
    detail.value ? buildAgentVerificationMessageGroups(detail.value) : [],
  );

  const loadDetail = async () => {
    loading.value = true;
    error.value = "";
    actionError.value = "";

    try {
      detail.value = await getAgentDetail(agentId.value);
    } catch (loadError) {
      error.value =
        loadError instanceof Error ? loadError.message : "Agent 详情加载失败。";
    } finally {
      loading.value = false;
    }
  };

  const handleVerify = async () => {
    if (!detail.value) {
      return;
    }

    busyAction.value = "verify";
    actionError.value = "";
    try {
      await verifyAgent(detail.value.agentId);
      await loadDetail();
    } catch (verifyError) {
      actionError.value =
        verifyError instanceof Error ? verifyError.message : "Agent 验证失败。";
    } finally {
      busyAction.value = "";
    }
  };

  const handleArchive = async () => {
    if (!detail.value) {
      return;
    }

    busyAction.value = "archive";
    actionError.value = "";
    try {
      await archiveAgent(detail.value.agentId);
      archiveDialogVisible.value = false;
      await router.push(RouteLocation.agentManagement);
    } catch (archiveError) {
      actionError.value =
        archiveError instanceof Error
          ? archiveError.message
          : "Agent 归档失败。";
    } finally {
      busyAction.value = "";
    }
  };

  onMounted(async () => {
    await loadDetail();
  });

  return {
    detail,
    loading,
    error,
    actionError,
    busyAction,
    archiveDialogVisible,
    busy,
    verificationLabel,
    verificationResultLabel,
    verificationResultIcon,
    summaryItems,
    connectionItems,
    authItems,
    inputMappingItems,
    outputMappingItems,
    statusItems,
    customRequestBodyJson,
    verificationStatItems,
    verificationMessageGroups,
    loadDetail,
    handleVerify,
    handleArchive,
  };
};
