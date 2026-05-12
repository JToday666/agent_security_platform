<template>
  <aside class="detail-actions">
    <div class="detail-actions__head">
      <span>{{ t("agent.management.currentStatus") }}</span>
      <AgentStatusTag :status="detail.status" size="sm" />
    </div>
    <dl class="detail-actions__meta">
      <div>
        <dt>{{ t("agent.detail.items.recentVerification") }}</dt>
        <dd>{{ verificationLabel }}</dd>
      </div>
      <div>
        <dt>{{ t("agent.detail.items.invokeMode") }}</dt>
        <dd>{{ invokeModeLabel }}</dd>
      </div>
    </dl>
    <UiButton
      variant="secondary"
      block
      leading-icon="app:action.verify"
      :disabled="!detail.actions.canVerify || busy"
      :loading="busyAction === 'verify'"
      @click="$emit('verify')"
    >
      {{ t("agent.actions.verify") }}
    </UiButton>
    <UiButton
      :to="RouteLocation.agentRegister({ copyFrom: detail.agentId })"
      variant="secondary"
      block
      leading-icon="app:action.copyNew"
    >
      {{ t("agent.actions.copyNew") }}
    </UiButton>
    <UiButton
      :to="RouteLocation.agentSubmitWithAgent(detail.agentId)"
      variant="primary"
      block
      leading-icon="app:action.submitEvaluation"
      :disabled="!detail.actions.canSubmitEvaluation"
    >
      {{ t("common.actions.submitEvaluation") }}
    </UiButton>
    <UiButton
      variant="danger"
      block
      leading-icon="app:action.archive"
      :disabled="!detail.actions.canArchive || busy"
      :loading="busyAction === 'archive'"
      @click="$emit('archive')"
    >
      {{ t("agent.actions.archive") }}
    </UiButton>
    <InlineNotice
      v-if="actionError"
      tone="danger"
      :message="actionError"
    />
  </aside>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import { RouteLocation } from "@/app/router/route-names";
import AgentStatusTag from "@/modules/agent/components/AgentStatusTag.vue";
import { getInvokeModeLabel } from "@/modules/agent/model/agent-display";
import type { AgentDetail } from "@/shared/types/agent-registry-types";
import UiButton from "@/shared/ui/actions/UiButton.vue";
import InlineNotice from "@/shared/ui/feedback/InlineNotice.vue";

const props = defineProps<{
  detail: AgentDetail;
  verificationLabel: string;
  busy: boolean;
  busyAction: "verify" | "archive" | "";
  actionError: string;
}>();

const { t } = useI18n();

defineEmits<{
  (event: "verify"): void;
  (event: "archive"): void;
}>();

const invokeModeLabel = computed(() => getInvokeModeLabel(props.detail.invokeMode, t));
</script>

<style scoped lang="scss">
.detail-actions {
  position: sticky;
  top: calc(var(--nav-height, 4rem) + 1.25rem);
  align-self: start;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding-top: 1rem;
  border-top: 1px solid var(--color-border-soft);
}

.detail-actions__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  color: var(--color-text-dark);
  font-weight: 800;
}

.detail-actions__meta {
  display: grid;
  gap: 0.7rem;
  margin: 0;
  padding: 0.8rem 0;
  border-block: 1px solid var(--color-border-soft);
}

.detail-actions__meta dt {
  color: var(--color-text-subtle);
  font-size: 0.86rem;
}

.detail-actions__meta dd {
  margin: 0.32rem 0 0;
  color: var(--color-text-dark);
  font-weight: 700;
  overflow-wrap: anywhere;
  line-height: 1.55;
}

@media (max-width: 1080px) {
  .detail-actions {
    position: static;
  }
}
</style>
