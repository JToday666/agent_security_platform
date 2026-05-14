<template>
  <Tag
    class="status-tag"
    :class="{ 'status-tag--icon-only': iconOnly }"
    :tone="resolved.tone"
    :size="resolvedSize"
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
  getEvaluationStatusIcon,
  getEvaluationStatusLabel,
  getEvaluationStatusTagTone,
} from "@/modules/evaluation/lib/evaluation-status";
import type { AppIconName } from "@/shared/ui/branding/app-icon-registry";

type StatusTagTone =
  | "neutral"
  | "brand"
  | "info"
  | "success"
  | "warning"
  | "danger"
  | "muted";

type ReportTagValue = "available" | "pending" | "missing";

interface StatusTagBaseProps {
  size?: "sm" | "md";
  iconOnly?: boolean;
}

type StatusTagProps = StatusTagBaseProps &
  (
    | {
        kind: "evaluation";
        value: EvaluationStatus;
      }
    | {
        kind: "leaderboard";
        value: LeaderboardVisibilityStatus;
      }
    | {
        kind: "method";
        value: SubmitMethod;
      }
    | {
        kind: "report";
        value: ReportTagValue;
      }
  );

interface ResolvedStatusTag {
  label: string;
  tone: StatusTagTone;
  icon: AppIconName;
}

const props = defineProps<StatusTagProps>();

const { t } = useI18n();
const resolvedSize = computed(() => props.size ?? "md");
const iconOnly = computed(() => props.iconOnly ?? false);

const resolved = computed<ResolvedStatusTag>(() => {
  if (props.kind === "evaluation") {
    return {
      label: getEvaluationStatusLabel(props.value, t),
      tone: getEvaluationStatusTagTone(props.value),
      icon: getEvaluationStatusIcon(props.value),
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

  if (props.kind === "report" && props.value === "available") {
    return {
      label: t("common.status.ready"),
      tone: "success" as const,
      icon: "app:status.available",
    };
  }

  if (props.kind === "report" && props.value === "pending") {
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
