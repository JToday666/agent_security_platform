<template>
  <article class="workflow-step">
    <div class="workflow-step__top">
      <span class="workflow-step__index">
        {{ t("common.units.step", { step }) }}
      </span>
      <AppIcon :icon="icon" class="workflow-step__icon" />
    </div>
    <div class="workflow-step__body">
      <h3 class="workflow-step__title">{{ title }}</h3>
      <p class="workflow-step__description">{{ description }}</p>
      <Button :to="to" variant="text" size="sm">
        {{ actionLabel }}
      </Button>
    </div>
  </article>
</template>

<script setup lang="ts">
import type { RouteLocationRaw } from "vue-router";
import { useI18n } from "vue-i18n";
import AppIcon from "@/shared/ui/branding/AppIcon.vue";
import Button from "@/shared/ui/actions/UiButton.vue";
import type { AppIconName } from "@/shared/ui/branding/app-icon-registry";

const { t } = useI18n();

defineProps<{
  step: number;
  icon: AppIconName;
  title: string;
  description: string;
  actionLabel: string;
  to: RouteLocationRaw;
}>();
</script>

<style scoped lang="scss">
.workflow-step {
  position: relative;
  display: flex;
  min-width: 0;
  min-height: 12.25rem;
  flex-direction: column;
  gap: 0.85rem;
  padding: 1rem;
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: var(--radius-control-sm);
  background: rgba(255, 255, 255, 0.72);
  box-shadow: var(--shadow-surface-soft);
}

.workflow-step__top {
  display: flex;
  min-width: 0;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.workflow-step__index {
  color: var(--color-text-subtle);
  font-size: 0.82rem;
  font-weight: 700;
  line-height: 1.4;
  overflow-wrap: anywhere;
}

.workflow-step__icon {
  width: 1.25rem;
  height: 1.25rem;
  flex: 0 0 auto;
  color: #4f46e5;
}

.workflow-step__body {
  display: flex;
  min-width: 0;
  flex-direction: column;
  flex: 1;
  gap: 0.72rem;
}

.workflow-step__title {
  margin: 0;
  color: var(--color-text-dark);
  font-size: 1.08rem;
  line-height: 1.42;
  overflow-wrap: anywhere;
}

.workflow-step__description {
  margin: 0;
  flex: 1;
  color: var(--color-text-muted);
  line-height: 1.72;
  overflow-wrap: anywhere;
}

.workflow-step :deep(.ui-button) {
  align-self: flex-start;
}

@media (max-width: 768px) {
  .workflow-step {
    min-height: auto;
  }
}
</style>
