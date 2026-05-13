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
import { useI18n } from "vue-i18n";
import type {
  EvaluationStatus,
  LeaderboardVisibilityStatus,
  SubmitMethod,
} from "@/shared/types/agent-types";
import AppIcon from "../branding/AppIcon.vue";
import Tag from "./UiTag.vue";
import {
  getEvaluationStatusLabel,
  getEvaluationStatusTone,
} from "@/modules/evaluation/lib/evaluation-status";

type StatusTagKind =
  | "evaluation"
  | "leaderboard"
  | "method"
  | "report";

const props = withDefaults(
  defineProps<{
    kind: StatusTagKind;
    value:
      | EvaluationStatus
      | SubmitMethod
      | LeaderboardVisibilityStatus
      | "available"
      | "pending"
      | "missing"
      | boolean;
    size?: "sm" | "md";
    iconOnly?: boolean;
  }>(),
  {
    size: "md",
    iconOnly: false,
  },
);

const { t } = useI18n();

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
      label: getEvaluationStatusLabel(status, t),
      tone:
        toneMap[toneKey as keyof typeof toneMap] ??
        ("neutral" as const),
      icon:
        status === "completed"
          ? "app:status.completed"
            : status === "running"
              ? "app:status.running"
              : status === "paused"
                ? "app:status.paused"
                : status === "pending" || status === "queued"
                  ? "app:status.pending"
                : status === "terminated"
                  ? "app:status.terminated"
                  : status === "canceled"
                    ? "app:status.canceled"
                    : "app:status.failed",
    };
  }

  if (props.kind === "leaderboard") {
    const value = props.value as LeaderboardVisibilityStatus;
    if (value === "anonymous") {
      return {
        label: t("common.status.anonymous"),
        tone: "info" as const,
        icon: "app:status.anonymous",
      };
    }

    if (value === "unranked") {
      return {
        label: t("common.status.rankedOut"),
        tone: "muted" as const,
        icon: "app:status.rankedOut",
      };
    }

    return {
      label: t("common.status.public"),
      tone: "brand" as const,
      icon: "app:status.public",
    };
  }

  if (props.kind === "method") {
    return props.value === "docker"
      ? { label: "Docker", tone: "brand" as const, icon: "app:method.docker" }
      : { label: "API", tone: "info" as const, icon: "app:method.api" };
  }

  if (props.value === "available") {
    return {
      label: t("common.status.ready"),
      tone: "success" as const,
      icon: "app:status.available",
    };
  }

  if (props.value === "pending") {
    return {
      label: t("common.status.running"),
      tone: "warning" as const,
      icon: "app:status.reportPending",
    };
  }

  return {
    label: t("common.status.notGenerated"),
    tone: "muted" as const,
    icon: "app:status.notGenerated",
  };
});
</script>

<style scoped lang="scss">
.status-tag--icon-only {
  padding-inline: 0.48rem;
}

.status-tag__icon {
  width: 0.95rem;
  height: 0.95rem;
  flex: 0 0 auto;
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
