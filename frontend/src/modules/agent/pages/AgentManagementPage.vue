<template>
  <div class="content agent-page layout-page-shell layout-page-shell--wide">
    <PageHero
      title="智能体管理"
      description="查看已注册 Agent 的状态，并执行验证、归档、复制新建和提交评测。"
      description-wrap="single-line"
    >
      <template #actions>
        <UiButton
          :to="RouteLocation.agentRegister()"
          variant="primary"
          leading-icon="lucide:bot-message-square"
        >
          注册智能体
        </UiButton>
      </template>
    </PageHero>

    <PageStatePanel
      v-if="loading"
      title="正在读取 Agent"
      message="请稍候。"
      :loading="true"
    />

    <PageStatePanel
      v-else-if="error"
      title="Agent 加载失败"
      :message="error"
      action-text="重试"
      @action="loadAgents"
    />

    <section v-else class="agent-list">
      <div class="agent-list__summary">
        <span>{{ listSummaryText }}</span>
        <label class="archive-toggle">
          <input v-model="includeArchived" type="checkbox" />
          <span>显示已归档</span>
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
                {{ getInvokeModeLabel(agent.invokeMode) }}
              </UiTag>
            </div>
          </div>
          <p>{{ agent.description || "暂无描述" }}</p>
          <span class="agent-row__meta">
            最近验证：{{ formatVerification(agent) }}
          </span>
        </div>

        <div class="agent-row__actions">
          <UiButton
            :to="RouteLocation.agentDetail(agent.agentId)"
            variant="secondary"
            size="sm"
            leading-icon="lucide:eye"
          >
            详情
          </UiButton>
          <UiButton
            variant="secondary"
            size="sm"
            leading-icon="lucide:rotate-cw"
            :disabled="!agent.canVerify || busyAgentId === agent.agentId"
            :loading="busyAgentId === agent.agentId && busyAction === 'verify'"
            @click="handleVerify(agent.agentId)"
          >
            验证
          </UiButton>
          <UiButton
            :to="RouteLocation.agentRegister({ copyFrom: agent.agentId })"
            variant="secondary"
            size="sm"
            leading-icon="lucide:copy-plus"
          >
            复制新建
          </UiButton>
          <UiButton
            :to="RouteLocation.agentSubmitWithAgent(agent.agentId)"
            variant="primary"
            size="sm"
            leading-icon="lucide:file-plus-2"
            :disabled="!agent.canSubmitEvaluation"
          >
            提交评测
          </UiButton>
          <UiButton
            variant="danger"
            size="sm"
            leading-icon="lucide:archive"
            :disabled="!agent.canArchive || busyAgentId === agent.agentId"
            :loading="busyAgentId === agent.agentId && busyAction === 'archive'"
            @click="openArchiveDialog(agent)"
          >
            归档
          </UiButton>
        </div>
      </article>

      <PageStatePanel
        v-if="agents.length === 0"
        :title="emptyStateTitle"
        :message="emptyStateMessage"
        action-text="注册智能体"
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
      title="归档 Agent"
      :message="archiveDialogMessage"
      confirm-text="确认归档"
      cancel-text="取消"
      :loading="busyAction === 'archive'"
      @confirm="confirmArchive"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
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
import { formatDateTimeLabel } from "@/modules/dataset/lib/dataset-utils";
import UiButton from "@/shared/ui/actions/UiButton.vue";
import UiTag from "@/shared/ui/display/UiTag.vue";
import ConfirmDialog from "@/shared/ui/feedback/ConfirmDialog.vue";
import InlineNotice from "@/shared/ui/feedback/InlineNotice.vue";
import PageStatePanel from "@/shared/ui/feedback/PageStatePanel.vue";
import PageHero from "@/shared/ui/page/PageHero.vue";

const $router = useRouter();
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
    ? `归档后，${archiveAgentTarget.value.name} 不能再提交评测，但仍可复制新建。`
    : "",
);
const listSummaryText = computed(() =>
  agents.value.length > 0
    ? `显示 ${agents.value.length} 个 Agent`
    : includeArchived.value
      ? "暂无 Agent"
      : "暂无可显示 Agent",
);
const emptyStateTitle = computed(() =>
  includeArchived.value ? "还没有 Agent" : "当前没有可显示 Agent",
);
const emptyStateMessage = computed(() =>
  includeArchived.value
    ? "注册并验证 Agent 后即可创建评测任务。"
    : "可切换显示已归档，或注册新的智能体。",
);

const formatVerification = (agent: AgentListItem): string => {
  if (!agent.verifiedAt) {
    return "未验证";
  }

  const result =
    agent.lastVerificationPassed === true
      ? "通过"
      : agent.lastVerificationPassed === false
        ? "失败"
        : "未知";
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
      loadError instanceof Error ? loadError.message : "Agent 加载失败。";
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
      verifyError instanceof Error ? verifyError.message : "Agent 验证失败。";
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
      archiveError instanceof Error ? archiveError.message : "Agent 归档失败。";
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
}

.agent-row__title h2 {
  margin: 0;
  color: var(--color-text-dark);
  font-size: 1.08rem;
  line-height: 1.35;
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
