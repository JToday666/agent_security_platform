<template>
  <InlineNotice
    v-if="createdAgent"
    tone="success"
    :title="t('agent.register.createSuccessTitle')"
    :message="t('agent.register.createSuccessMessage')"
  >
    <template #actions>
      <UiButton
        variant="secondary"
        size="sm"
        :loading="verifying"
        leading-icon="app:action.verify"
        @click="$emit('verify')"
      >
        {{ t("agent.actions.verifyNow") }}
      </UiButton>
      <UiButton
        :to="RouteLocation.agentDetail(createdAgent.agentId)"
        variant="primary"
        size="sm"
        leading-icon="app:action.details"
      >
        {{ t("agent.actions.viewDetails") }}
      </UiButton>
    </template>
  </InlineNotice>
</template>

<script setup lang="ts">
import { useI18n } from "vue-i18n";
import { RouteLocation } from "@/app/router/route-names";
import type { AgentCreateResponse } from "@/shared/types/agent-registry-types";
import UiButton from "@/shared/ui/actions/UiButton.vue";
import InlineNotice from "@/shared/ui/feedback/InlineNotice.vue";

defineProps<{
  createdAgent: AgentCreateResponse | null;
  verifying: boolean;
}>();

defineEmits<{
  (event: "verify"): void;
}>();

const { t } = useI18n();
</script>
