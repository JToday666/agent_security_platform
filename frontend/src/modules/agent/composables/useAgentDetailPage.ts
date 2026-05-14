import { computed, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
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
import { getErrorMessage } from "@/shared/composables/useAsyncState";
import type { AgentDetail } from "@/shared/types/agent-registry-types";
import type { AppIconName } from "@/shared/ui/branding/app-icon-registry";

export const useAgentDetailPage = () => {
  const route = useRoute();
  const router = useRouter();
  const { t } = useI18n();

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
    detail.value
      ? formatAgentVerificationLabel(detail.value, t)
      : t("agent.verification.notVerified"),
  );
  const verificationResultLabel = computed(() =>
    detail.value ? getAgentVerificationResultLabel(detail.value, t) : "",
  );
  const verificationResultIcon = computed<AppIconName>(() =>
    detail.value
      ? getAgentVerificationResultIcon(detail.value)
      : "app:status.warning",
  );
  const summaryItems = computed(() =>
    detail.value ? buildAgentSummaryItems(detail.value, t) : [],
  );
  const connectionItems = computed(() =>
    detail.value ? buildAgentConnectionItems(detail.value, t) : [],
  );
  const authItems = computed(() =>
    detail.value ? buildAgentAuthItems(detail.value, t) : [],
  );
  const inputMappingItems = computed(() =>
    detail.value
      ? buildAgentInputMappingItems(detail.value.platformInputMapping, t)
      : [],
  );
  const outputMappingItems = computed(() =>
    detail.value
      ? buildAgentOutputMappingItems(detail.value.platformOutputMapping, t)
      : [],
  );
  const statusItems = computed(() =>
    detail.value ? buildAgentStatusItems(detail.value, t) : [],
  );
  const customRequestBodyJson = computed(() =>
    detail.value ? buildAgentCustomRequestBodyJson(detail.value) : "{}",
  );
  const verificationStatItems = computed(() =>
    detail.value ? buildAgentVerificationStatItems(detail.value, t) : [],
  );
  const verificationMessageGroups = computed(() =>
    detail.value ? buildAgentVerificationMessageGroups(detail.value, t) : [],
  );

  const loadDetail = async () => {
    loading.value = true;
    error.value = "";
    actionError.value = "";

    try {
      detail.value = await getAgentDetail(agentId.value);
    } catch (loadError) {
      error.value =
        getErrorMessage(loadError, t("agent.api.detailLoadFailed"));
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
        getErrorMessage(verifyError, t("agent.api.verifyFailed"));
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
        getErrorMessage(archiveError, t("agent.api.archiveFailed"));
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
