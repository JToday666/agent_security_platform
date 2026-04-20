<template>
  <section
    class="page-state-card layout-state-card ui-surface-white"
    :class="[
      `page-state-card--${tone}`,
      { 'page-state-card--loading': loading },
    ]"
  >
    <h2 class="page-state-card__title">{{ title }}</h2>
    <p class="page-state-card__message">{{ message }}</p>

    <div v-if="$slots.default" class="page-state-card__extra">
      <slot />
    </div>

    <UiButton
      v-if="actionText"
      class="page-state-card__action"
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
.page-state-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
}

.page-state-card--loading {
  position: relative;
  overflow: hidden;
}

.page-state-card__title {
  margin: 0;
  color: var(--color-text-dark);
  font-size: 1.2rem;
}

.page-state-card__message {
  margin: 0;
  color: var(--color-text-subtle);
  line-height: 1.72;
}

.page-state-card__extra {
  display: flex;
  flex-direction: column;
  gap: 0.7rem;
}

.page-state-card__action {
  width: fit-content;
}

.page-state-card--danger {
  border-color: rgba(239, 68, 68, 0.12);
}

@media (max-width: 768px) {
  .page-state-card__action {
    width: 100%;
  }
}
</style>
