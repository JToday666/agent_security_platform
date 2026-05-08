<template>
  <aside class="detail-actions">
    <div class="detail-actions__head">
      <span>当前状态</span>
      <AgentStatusTag :status="detail.status" size="sm" />
    </div>
    <dl class="detail-actions__meta">
      <div>
        <dt>最近验证</dt>
        <dd>{{ verificationLabel }}</dd>
      </div>
      <div>
        <dt>调用模式</dt>
        <dd>{{ invokeModeLabel }}</dd>
      </div>
    </dl>
    <UiButton
      variant="secondary"
      block
      leading-icon="lucide:rotate-cw"
      :disabled="!detail.actions.canVerify || busy"
      :loading="busyAction === 'verify'"
      @click="$emit('verify')"
    >
      验证
    </UiButton>
    <UiButton
      :to="RouteLocation.agentRegister({ copyFrom: detail.agentId })"
      variant="secondary"
      block
      leading-icon="lucide:copy-plus"
    >
      复制新建
    </UiButton>
    <UiButton
      :to="RouteLocation.agentSubmitWithAgent(detail.agentId)"
      variant="primary"
      block
      leading-icon="lucide:file-plus-2"
      :disabled="!detail.actions.canSubmitEvaluation"
    >
      提交评测
    </UiButton>
    <UiButton
      variant="danger"
      block
      leading-icon="lucide:archive"
      :disabled="!detail.actions.canArchive || busy"
      :loading="busyAction === 'archive'"
      @click="$emit('archive')"
    >
      归档
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

defineEmits<{
  (event: "verify"): void;
  (event: "archive"): void;
}>();

const invokeModeLabel = computed(() => getInvokeModeLabel(props.detail.invokeMode));
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
