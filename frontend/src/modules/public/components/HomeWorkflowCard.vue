<template>
  <article class="workflow-card ui-surface-white ui-hover-card">
    <div class="workflow-top">
      <span class="workflow-step">步骤 {{ step }}</span>
      <AppIcon :icon="icon" class="workflow-icon" />
    </div>
    <h3>{{ title }}</h3>
    <p>{{ description }}</p>
    <Button :to="to" variant="text" size="sm">
      {{ actionLabel }}
    </Button>
  </article>
</template>

<script setup lang="ts">
import type { RouteLocationRaw } from "vue-router";
import AppIcon from "@/shared/ui/branding/AppIcon.vue";
import Button from "@/shared/ui/actions/UiButton.vue";

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
.workflow-card {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
  min-height: 220px;
  padding: 1.1rem;
  border-radius: 1.3rem;
}

.workflow-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.workflow-step {
  color: var(--color-text-subtle);
  font-size: 0.84rem;
  font-weight: 700;
}

.workflow-icon {
  width: 1.2rem;
  height: 1.2rem;
  color: var(--color-primary);
}

.workflow-card h3 {
  margin: 0;
  color: var(--color-text-dark);
  font-size: 1.12rem;
}

.workflow-card p {
  margin: 0;
  flex: 1;
  color: var(--color-text-muted);
  line-height: 1.72;
}
</style>
