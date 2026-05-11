<template>
  <article class="workflow-step">
    <div class="workflow-step__top">
      <span class="workflow-step__index">
        {{ t("common.units.step", { step }) }}
      </span>
      <AppIcon :icon="icon" class="workflow-step__icon" />
    </div>
    <h3 class="workflow-step__title">{{ title }}</h3>
    <p class="workflow-step__description">{{ description }}</p>
    <Button :to="to" variant="text" size="sm">
      {{ actionLabel }}
    </Button>
  </article>
</template>

<script setup lang="ts">
import type { RouteLocationRaw } from "vue-router";
import { useI18n } from "vue-i18n";
import AppIcon from "@/shared/ui/branding/AppIcon.vue";
import Button from "@/shared/ui/actions/UiButton.vue";

const { t } = useI18n();

defineProps<{
  step: number;
  icon: string;
  title: string;
  description: string;
  actionLabel: string;
  to: RouteLocationRaw;
}>();
</script>

<style scoped lang="scss">
.workflow-step {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
  min-height: 220px;
  padding: 1.2rem 0 0.2rem;
  border-top: 1px solid rgba(148, 163, 184, 0.18);
}

.workflow-step__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.workflow-step__index {
  color: var(--color-text-subtle);
  font-size: 0.82rem;
  font-weight: 700;
}

.workflow-step__icon {
  width: 1.15rem;
  height: 1.15rem;
  color: #4f46e5;
}

.workflow-step__title {
  margin: 0;
  color: var(--color-text-dark);
  font-size: 1.08rem;
}

.workflow-step__description {
  margin: 0;
  flex: 1;
  color: var(--color-text-muted);
  line-height: 1.72;
}
</style>
