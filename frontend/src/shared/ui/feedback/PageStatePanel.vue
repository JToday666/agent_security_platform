<template>
  <section
    class="page-state-panel layout-state-card"
    :class="[
      `page-state-panel--${tone}`,
      { 'page-state-panel--loading': loading },
    ]"
  >
    <h2 class="page-state-panel__title">{{ title }}</h2>
    <p class="page-state-panel__message">{{ message }}</p>

    <div v-if="$slots.default" class="page-state-panel__extra">
      <slot />
    </div>

    <UiButton
      v-if="actionText"
      class="page-state-panel__action"
      :variant="actionVariant"
      :loading="loading"
      @click="$emit('action')"
    >
      {{ actionText }}
    </UiButton>
  </section>
</template>

<script setup lang="ts">
import UiButton from "../actions/UiButton.vue";

withDefaults(
  defineProps<{
    title: string;
    message: string;
    loading?: boolean;
    tone?: "default" | "danger";
    actionText?: string;
    actionVariant?: "primary" | "secondary" | "ghost" | "text" | "danger";
  }>(),
  {
    loading: false,
    tone: "default",
    actionText: "",
    actionVariant: "primary",
  },
);

defineEmits<{
  (event: "action"): void;
}>();
</script>

<style scoped lang="scss">
.page-state-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.8rem;
  min-width: 0;
  overflow-wrap: anywhere;
}

.page-state-panel--loading {
  position: relative;
  overflow: hidden;
}

.page-state-panel__title {
  margin: 0;
  color: var(--color-text-dark);
  font-size: 1.18rem;
  overflow-wrap: anywhere;
}

.page-state-panel__message {
  margin: 0;
  color: var(--color-text-subtle);
  line-height: 1.72;
  overflow-wrap: anywhere;
}

.page-state-panel__extra {
  display: flex;
  flex-direction: column;
  gap: 0.7rem;
  min-width: 0;
  max-width: 100%;
}

.page-state-panel__action {
  width: fit-content;
}

.page-state-panel--danger {
  border-color: rgba(239, 68, 68, 0.12);
}

@media (max-width: 768px) {
  .page-state-panel__action {
    width: 100%;
  }
}
</style>
