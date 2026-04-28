<template>
  <Tag
    class="status-tag"
    :class="{ 'status-tag--icon-only': iconOnly }"
    :tone="resolved.tone"
    :size="size"
  >
    <AppIcon
      v-if="resolved.icon"
      :icon="resolved.icon"
      :title="iconOnly ? resolved.label : undefined"
      :decorative="!iconOnly"
      class="status-tag__icon"
    />
    <template v-if="!iconOnly">{{ resolved.label }}</template>
    <span v-else class="status-tag__sr-only">{{ resolved.label }}</span>
  </Tag>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { EvaluationStatus, SubmitMethod } from "@/shared/types/agent-types";
import AppIcon from "../branding/AppIcon.vue";
import Tag from "./UiTag.vue";
import {
  getEvaluationStatusLabel,
  getEvaluationStatusTone,
} from "@/modules/evaluation/lib/evaluation-status";

type StatusTagKind = "evaluation" | "visibility" | "method" | "report";

const props = withDefaults(
  defineProps<{
    kind: StatusTagKind;
    value: EvaluationStatus | SubmitMethod | "available" | "pending" | "missing" | boolean;
    size?: "sm" | "md";
    iconOnly?: boolean;
  }>(),
  {
    size: "md",
    iconOnly: false,
  },
);

const resolved = computed(() => {
  if (props.kind === "evaluation") {
    const toneMap = {
      pending: "warning",
      running: "info",
      paused: "warning",
      completed: "success",
      terminated: "brand",
      canceled: "danger",
      failed: "danger",
    } as const;
    const status = props.value as EvaluationStatus;
    const toneKey = getEvaluationStatusTone(status);

    return {
      label: getEvaluationStatusLabel(status),
      tone:
        toneMap[toneKey as keyof typeof toneMap] ??
        ("neutral" as const),
      icon:
        status === "completed"
          ? "lucide:circle-check-big"
            : status === "running"
              ? "lucide:loader-circle"
              : status === "paused"
                ? "lucide:pause-circle"
                : status === "pending" || status === "queued"
                  ? "lucide:clock-3"
                : status === "terminated"
                  ? "lucide:octagon-x"
                  : status === "canceled"
                    ? "lucide:ban"
                    : "lucide:triangle-alert",
    };
  }

  if (props.kind === "visibility") {
    return props.value
      ? { label: "公开", tone: "brand" as const, icon: "lucide:globe" }
      : { label: "私有", tone: "muted" as const, icon: "lucide:lock" };
  }

  if (props.kind === "method") {
    return props.value === "docker"
      ? { label: "Docker", tone: "brand" as const, icon: "lucide:package" }
      : { label: "API", tone: "info" as const, icon: "lucide:plug-zap" };
  }

  if (props.value === "available") {
    return { label: "已生成", tone: "success" as const, icon: "lucide:file-check-2" };
  }

  if (props.value === "pending") {
    return { label: "生成中", tone: "warning" as const, icon: "lucide:file-clock" };
  }

  return { label: "未生成", tone: "muted" as const, icon: "lucide:file-minus" };
});
</script>

<style scoped lang="scss">
.status-tag--icon-only {
  padding-inline: 0.48rem;
}

.status-tag__icon {
  width: 0.95rem;
  height: 0.95rem;
}

.status-tag__sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
</style>
