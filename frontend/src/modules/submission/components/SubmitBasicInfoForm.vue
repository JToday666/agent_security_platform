<template>
  <SectionBlock
    :title="t('submission.agent.title')"
    :description="t('submission.agent.description')"
  >
    <InlineNotice
      v-if="form.submitMethod === 'docker'"
      tone="warning"
      :title="t('submission.agent.dockerUnavailableTitle')"
      :message="t('submission.agent.dockerUnavailableMessage')"
    />

    <div v-else class="agent-picker">
      <FormField
        :label="t('submission.agent.label')"
        type="select"
        :model-value="form.agentId"
        :options="agentOptions"
        :disabled="agentOptions.length === 0"
        :error="agentOptions.length > 0 ? agentErrorMessage : ''"
        :help="t('submission.agent.help')"
        :placeholder="t('submission.agent.placeholder')"
        leading-icon="app:field.agent"
        full
        @update:model-value="selectAgent"
      />

      <div
        v-if="selectedAgent"
        class="agent-picker__summary"
        aria-live="polite"
      >
        <span class="agent-picker__main">
          <strong>{{ selectedAgent.name }}</strong>
          <span>{{ selectedAgent.description || t("agent.common.noDescription") }}</span>
        </span>
        <span class="agent-picker__meta">
          <AgentStatusTag :status="selectedAgent.status" size="sm" />
          <span>{{ getInvokeModeLabel(selectedAgent.invokeMode, t) }}</span>
        </span>
      </div>

      <PageStatePanel
        v-if="agentOptions.length === 0"
        :title="t('submission.agent.emptyTitle')"
        :message="t('submission.agent.emptyMessage')"
        tone="default"
      />

      <InlineNotice
        v-if="agentErrorMessage && agentOptions.length === 0"
        tone="warning"
        :message="agentErrorMessage"
      />
    </div>
  </SectionBlock>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import type { AgentListItem } from "@/shared/types/agent-registry-types";
import type { SubmitFormState } from "@/shared/types/agent-types";
import AgentStatusTag from "@/modules/agent/components/AgentStatusTag.vue";
import { getInvokeModeLabel } from "@/modules/agent/model/agent-display";
import { buildSubmitAgentOptions } from "@/modules/submission/model/submit-agent-options";
import InlineNotice from "@/shared/ui/feedback/InlineNotice.vue";
import PageStatePanel from "@/shared/ui/feedback/PageStatePanel.vue";
import FormField from "@/shared/ui/forms/FormField.vue";
import SectionBlock from "@/shared/ui/page/SectionBlock.vue";

const props = withDefaults(
  defineProps<{
    agents: AgentListItem[];
    agentErrorMessage?: string;
  }>(),
  {
    agentErrorMessage: "",
  },
);

const emit = defineEmits<{
  (event: "select-agent", agentId: string): void;
}>();

const form = defineModel<SubmitFormState>({ required: true });
const { t } = useI18n();
const agentOptions = computed(() => buildSubmitAgentOptions(props.agents, t));
const selectedAgent = computed(
  () =>
    props.agents.find((agent) => agent.agentId === form.value.agentId) ?? null,
);

const selectAgent = (agentId: string) => {
  form.value.agentId = agentId;
  emit("select-agent", agentId);
};
</script>

<style scoped lang="scss">
.agent-picker {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.agent-picker__summary {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  min-width: 0;
  padding: 0.95rem 1rem;
  border: 1px solid var(--color-border-soft);
  border-radius: var(--radius-card-sm);
  background:
    radial-gradient(circle at 12% 0%, rgba(99, 102, 241, 0.1), transparent 32%),
    rgba(255, 255, 255, 0.74);
  box-shadow: var(--shadow-surface-soft);
  transition:
    border-color var(--duration-fast) var(--ease-standard),
    box-shadow var(--duration-fast) var(--ease-standard),
    transform var(--duration-fast) var(--ease-standard);
}

.agent-picker__summary:hover {
  border-color: var(--color-border-strong);
  box-shadow: var(--shadow-surface-hover);
  transform: translateY(-1px);
}

.agent-picker__main {
  min-width: 0;
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 0.38rem;
}

.agent-picker__main strong {
  color: var(--color-text-dark);
  font-size: 1rem;
}

.agent-picker__main span,
.agent-picker__meta span {
  color: var(--color-text-muted);
  line-height: 1.55;
}

.agent-picker__meta {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 0.55rem;
  flex-shrink: 0;
}

@media (max-width: 760px) {
  .agent-picker__summary,
  .agent-picker__meta {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
