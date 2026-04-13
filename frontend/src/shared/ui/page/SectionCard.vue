<template>
  <section class="section-card layout-section-card ui-surface-white" :class="{ 'section-card--compact': compact }">
    <div v-if="title || description || $slots.actions" class="section-card__head">
      <div class="section-card__copy">
        <h2 v-if="title" class="section-card__title">{{ title }}</h2>
        <p v-if="description" class="section-card__description">{{ description }}</p>
      </div>

      <div v-if="$slots.actions" class="section-card__actions">
        <slot name="actions" />
      </div>
    </div>

    <div class="section-card__body">
      <slot />
    </div>
  </section>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    title?: string;
    description?: string;
    compact?: boolean;
  }>(),
  {
    title: "",
    description: "",
    compact: false,
  },
);
</script>

<style scoped>
.section-card {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.section-card--compact {
  gap: 0.8rem;
}

.section-card__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.section-card__copy {
  min-width: 0;
}

.section-card__title {
  margin: 0;
  color: var(--color-text-dark);
  font-size: 1.12rem;
}

.section-card__description {
  margin: 0.42rem 0 0;
  color: var(--color-text-subtle);
  line-height: 1.7;
}

.section-card__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem;
  flex-shrink: 0;
}

.section-card__body {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

@media (max-width: 768px) {
  .section-card__head {
    flex-direction: column;
  }

  .section-card__actions {
    width: 100%;
  }
}
</style>
