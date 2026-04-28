<template>
  <UiTag :tone="tone" :size="size" class="agent-status-tag">
    <AppIcon :icon="icon" class="agent-status-tag__icon" aria-hidden="true" />
    {{ label }}
  </UiTag>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { AgentStatus } from "@/shared/types/agent-registry-types";
import AppIcon from "@/shared/ui/branding/AppIcon.vue";
import UiTag from "@/shared/ui/display/UiTag.vue";
import {
  getAgentStatusIcon,
  getAgentStatusLabel,
  getAgentStatusTone,
} from "@/modules/agent/model/agent-display";

const props = withDefaults(
  defineProps<{
    status: AgentStatus;
    size?: "sm" | "md";
  }>(),
  {
    size: "md",
  },
);

const label = computed(() => getAgentStatusLabel(props.status));
const tone = computed(() => getAgentStatusTone(props.status));
const icon = computed(() => getAgentStatusIcon(props.status));
</script>

<style scoped lang="scss">
.agent-status-tag__icon {
  width: 0.95rem;
  height: 0.95rem;
}
</style>
