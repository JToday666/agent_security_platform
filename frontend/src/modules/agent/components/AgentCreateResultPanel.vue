<template>
  <InlineNotice
    v-if="createdAgent"
    tone="success"
    title="Agent 已创建"
    message="验证通过后可用于提交评测。"
  >
    <template #actions>
      <UiButton
        variant="secondary"
        size="sm"
        :loading="verifying"
        leading-icon="lucide:rotate-cw"
        @click="$emit('verify')"
      >
        立即验证
      </UiButton>
      <UiButton
        :to="RouteLocation.agentDetail(createdAgent.agentId)"
        variant="primary"
        size="sm"
        leading-icon="lucide:eye"
      >
        查看详情
      </UiButton>
    </template>
  </InlineNotice>
</template>

<script setup lang="ts">
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
</script>
