<template>
  <div class="content agent-page layout-page-shell layout-page-shell--wide">
    <PageHero
      :title="t('agent.management.title')"
      :description="t('agent.management.description')"
      description-wrap="single-line"
    >
      <template #actions>
        <UiButton
          :to="RouteLocation.agentRegister()"
          variant="primary"
          leading-icon="app:action.registerAgent"
        >
          {{ t("agent.actions.registerAgent") }}
        </UiButton>
      </template>
    </PageHero>

    <PageStatePanel
      v-if="loading"
      :title="t('agent.detail.loadingTitle')"
      :message="t('common.feedback.pleaseWait')"
      :loading="true"
    />

    <PageStatePanel
      v-else-if="error"
      :title="t('agent.detail.errorTitle')"
      :message="error"
      :action-text="t('common.actions.retry')"
      @action="loadAgents"
    />

    <section v-else class="agent-list">
      <div class="agent-list__summary">
        <span>{{ listSummaryText }}</span>
        <label class="archive-toggle">
          <input v-model="includeArchived" type="checkbox" />
          <span>{{ t("agent.management.includeArchived") }}</span>
        </label>
      </div>

      <article
        v-for="agent in agents"
        :key="agent.agentId"
        class="agent-row"
      >
        <div class="agent-row__main">
          <div class="agent-row__title">
            <h2>{{ agent.name }}</h2>
            <div class="agent-row__tags">
              <AgentStatusTag :status="agent.status" size="sm" />
              <UiTag tone="info" size="sm">
                {{ getInvokeModeLabel(agent.invokeMode, t) }}
              </UiTag>
            </div>
          </div>
          <p>{{ agent.description || t("agent.common.noDescription") }}</p>
          <span class="agent-row__meta">
            {{ t("agent.management.recentVerification", { value: formatVerification(agent) }) }}
          </span>
        </div>

        <div class="agent-row__actions">
          <UiButton
            :to="RouteLocation.agentDetail(agent.agentId)"
            variant="secondary"
            size="sm"
            leading-icon="app:action.details"
          >
            {{ t("agent.actions.details") }}
          </UiButton>
          <UiButton
            variant="secondary"
            size="sm"
            leading-icon="app:action.verify"
            :disabled="!agent.canVerify || busyAgentId === agent.agentId"
            :loading="busyAgentId === agent.agentId && busyAction === 'verify'"
            @click="handleVerify(agent.agentId)"
          >
            {{ t("agent.actions.verify") }}
          </UiButton>
          <UiButton
            :to="RouteLocation.agentRegister({ copyFrom: agent.agentId })"
            variant="secondary"
            size="sm"
            leading-icon="app:action.copyNew"
          >
            {{ t("agent.actions.copyNew") }}
          </UiButton>
          <UiButton
            :to="RouteLocation.agentSubmitWithAgent(agent.agentId)"
            variant="primary"
            size="sm"
            leading-icon="app:action.submitEvaluation"
            :disabled="!agent.canSubmitEvaluation"
          >
            {{ t("common.actions.submitEvaluation") }}
          </UiButton>
          <UiButton
            variant="danger"
            size="sm"
            leading-icon="app:action.archive"
            :disabled="!agent.canArchive || busyAgentId === agent.agentId"
            :loading="busyAgentId === agent.agentId && busyAction === 'archive'"
            @click="openArchiveDialog(agent)"
          >
            {{ t("agent.actions.archive") }}
          </UiButton>
        </div>
      </article>

      <PageStatePanel
        v-if="agents.length === 0"
        :title="emptyStateTitle"
        :message="emptyStateMessage"
        :action-text="t('agent.actions.registerAgent')"
        @action="$router.push(RouteLocation.agentRegister())"
      />
    </section>

    <InlineNotice
      v-if="actionError"
      class="agent-page__notice"
      tone="danger"
      :message="actionError"
    />

    <ConfirmDialog
      v-model="archiveDialogVisible"
      :title="t('agent.detail.archiveDialogTitle')"
      :message="archiveDialogMessage"
      :confirm-text="t('agent.detail.confirmArchive')"
      :cancel-text="t('common.actions.cancel')"
      :loading="busyAction === 'archive'"
      @confirm="confirmArchive"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { useRouter } from "vue-router";
import { RouteLocation } from "@/app/router/route-names";
import {
  archiveAgent,
  getAgents,
  verifyAgent,
} from "@/modules/agent/api/agent-api";
import AgentStatusTag from "@/modules/agent/components/AgentStatusTag.vue";
import { getInvokeModeLabel } from "@/modules/agent/model/agent-display";
import type { AgentListItem } from "@/shared/types/agent-registry-types";
import { formatDateTimeLabel } from "@/modules/attack-scenario-library/lib/attack-scenario-library-utils";
import { getErrorMessage } from "@/shared/composables/useAsyncState";
import UiButton from "@/shared/ui/actions/UiButton.vue";
import UiTag from "@/shared/ui/display/UiTag.vue";
import ConfirmDialog from "@/shared/ui/feedback/ConfirmDialog.vue";
import InlineNotice from "@/shared/ui/feedback/InlineNotice.vue";
import PageStatePanel from "@/shared/ui/feedback/PageStatePanel.vue";
import PageHero from "@/shared/ui/page/PageHero.vue";

const $router = useRouter();
const { t } = useI18n();
const agents = ref<AgentListItem[]>([]);
const loading = ref(true);
const error = ref("");
const actionError = ref("");
const includeArchived = ref(false);
const busyAgentId = ref("");
const busyAction = ref<"verify" | "archive" | "">("");
const archiveDialogVisible = ref(false);
const archiveAgentTarget = ref<AgentListItem | null>(null);

const archiveDialogMessage = computed(() =>
  archiveAgentTarget.value
    ? t("agent.management.archiveDialogMessage", {
        name: archiveAgentTarget.value.name,
      })
    : "",
);
const listSummaryText = computed(() =>
  agents.value.length > 0
    ? t("agent.management.listSummaryWithCount", { count: agents.value.length })
    : includeArchived.value
      ? t("agent.management.listSummaryEmpty")
      : t("agent.management.listSummaryNoVisible"),
);
const emptyStateTitle = computed(() =>
  includeArchived.value
    ? t("agent.management.emptyTitleArchived")
    : t("agent.management.emptyTitleVisible"),
);
const emptyStateMessage = computed(() =>
  includeArchived.value
    ? t("agent.management.emptyMessageArchived")
    : t("agent.management.emptyMessageVisible"),
);

const formatVerification = (agent: AgentListItem): string => {
  if (!agent.verifiedAt) {
    return t("agent.verification.notVerified");
  }

  const result =
    agent.lastVerificationPassed === true
      ? t("agent.verification.passed")
      : agent.lastVerificationPassed === false
        ? t("agent.verification.failed")
        : t("agent.common.unknown");
  return `${formatDateTimeLabel(agent.verifiedAt)} · ${result}`;
};

const loadAgents = async () => {
  loading.value = true;
  error.value = "";

  try {
    agents.value = await getAgents({
      includeArchived: includeArchived.value,
    });
  } catch (loadError) {
    error.value =
      getErrorMessage(loadError, t("agent.api.loadFailed"));
  } finally {
    loading.value = false;
  }
};

const handleVerify = async (agentId: string) => {
  busyAgentId.value = agentId;
  busyAction.value = "verify";
  actionError.value = "";

  try {
    await verifyAgent(agentId);
    await loadAgents();
  } catch (verifyError) {
    actionError.value =
      getErrorMessage(verifyError, t("agent.api.verifyFailed"));
  } finally {
    busyAgentId.value = "";
    busyAction.value = "";
  }
};

const openArchiveDialog = (agent: AgentListItem) => {
  archiveAgentTarget.value = agent;
  archiveDialogVisible.value = true;
};

const confirmArchive = async () => {
  if (!archiveAgentTarget.value) {
    return;
  }

  busyAgentId.value = archiveAgentTarget.value.agentId;
  busyAction.value = "archive";
  actionError.value = "";

  try {
    await archiveAgent(archiveAgentTarget.value.agentId);
    archiveDialogVisible.value = false;
    archiveAgentTarget.value = null;
    await loadAgents();
  } catch (archiveError) {
    actionError.value =
      getErrorMessage(archiveError, t("agent.api.archiveFailed"));
  } finally {
    busyAgentId.value = "";
    busyAction.value = "";
  }
};

watch(includeArchived, () => {
  void loadAgents();
});

onMounted(async () => {
  await loadAgents();
});
</script>

<style scoped lang="scss">
.agent-page {
  padding-bottom: 2.5rem;
}

.agent-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.agent-list__summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  min-height: 2.5rem;
  color: var(--color-text-muted);
  font-size: 0.92rem;
}

.archive-toggle {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  min-height: 2.5rem;
  color: var(--color-text-main);
  font-weight: 600;
  cursor: pointer;
  transition: color var(--duration-fast) var(--ease-standard);
}

.archive-toggle:hover {
  color: var(--color-primary);
}

.archive-toggle input {
  width: 1rem;
  height: 1rem;
  accent-color: var(--color-primary);
}

.agent-row {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 1.25rem;
  min-width: 0;
  padding: 1.05rem 0.85rem 0.95rem;
  border-top: 1px solid var(--color-border-soft);
  border-radius: var(--radius-card-sm);
  transition:
    background var(--duration-fast) var(--ease-standard),
    border-color var(--duration-fast) var(--ease-standard),
    box-shadow var(--duration-fast) var(--ease-standard),
    transform var(--duration-fast) var(--ease-standard);
}

.agent-row::before {
  position: absolute;
  inset: 0 auto 0 0;
  width: 3px;
  content: "";
  border-radius: var(--radius-pill);
  background: var(--grad-primary);
  opacity: 0;
  transform: scaleY(0.55);
  transform-origin: center;
  transition:
    opacity var(--duration-fast) var(--ease-standard),
    transform var(--duration-fast) var(--ease-standard);
}

.agent-row:hover,
.agent-row:focus-within {
  border-color: var(--color-border-strong);
  background:
    radial-gradient(circle at 0 0, rgba(99, 102, 241, 0.09), transparent 28%),
    rgba(255, 255, 255, 0.52);
  box-shadow: var(--shadow-surface-soft);
  transform: translateY(-1px);
}

.agent-row:hover::before,
.agent-row:focus-within::before {
  opacity: 1;
  transform: scaleY(1);
}

.agent-row__main {
  min-width: 0;
  padding-left: 0.35rem;
}

.agent-row__title {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  min-width: 0;
}

.agent-row__title h2 {
  margin: 0;
  min-width: 0;
  color: var(--color-text-dark);
  font-size: 1.08rem;
  line-height: 1.35;
  overflow-wrap: anywhere;
}

.agent-row__tags,
.agent-row__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.55rem;
}

.agent-row__tags {
  justify-content: flex-end;
}

.agent-row__main p,
.agent-row__meta {
  margin: 0.55rem 0 0;
  color: var(--color-text-muted);
  line-height: 1.65;
}

.agent-row__meta {
  display: inline-flex;
  align-items: center;
  min-height: 1.5rem;
}

.agent-row__actions {
  justify-content: flex-end;
  align-self: start;
  max-width: 28rem;
  min-width: 0;
}

.agent-page__notice {
  margin-top: 1rem;
}

@media (max-width: 980px) {
  .agent-row {
    grid-template-columns: 1fr;
  }

  .agent-row__actions,
  .agent-row__tags {
    justify-content: flex-start;
  }
}

@media (max-width: 640px) {
  .agent-list__summary,
  .agent-row__title {
    flex-direction: column;
    align-items: flex-start;
  }

  .agent-row {
    padding-inline: 0.75rem;
  }
}
</style>
