<template>
  <section
    class="section-block layout-section-card"
    :class="[
      `section-block--${surface}`,
      { 'section-block--compact': compact },
    ]"
  >
    <div
      v-if="title || description || $slots.actions"
      class="section-block__head"
    >
      <div class="section-block__copy">
        <h2 v-if="title" class="section-block__title">{{ title }}</h2>
        <p v-if="description" class="section-block__description">
          {{ description }}
        </p>
      </div>

      <div v-if="$slots.actions" class="section-block__actions">
        <slot name="actions" />
      </div>
    </div>

    <div class="section-block__body">
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
    surface?: "line" | "panel";
  }>(),
  {
    title: "",
    description: "",
    compact: false,
    surface: "line",
  },
);
</script>

<style scoped lang="scss">
.section-block {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.section-block--compact {
  gap: 0.82rem;
}

.section-block--panel {
  padding: 1.2rem;
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: 1.35rem;
  background: rgba(255, 255, 255, 0.76);
  box-shadow: var(--shadow-surface-soft);
}

.section-block__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.section-block__copy {
  min-width: 0;
}

.section-block__title {
  margin: 0;
  color: var(--color-text-dark);
  font-size: 1.08rem;
}

.section-block__description {
  margin: 0.35rem 0 0;
  color: var(--color-text-subtle);
  line-height: 1.68;
}

.section-block__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem;
  flex-shrink: 0;
}

.section-block__body {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.section-block--panel .section-block__head {
  gap: 1.25rem;
}

@media (max-width: 768px) {
  .section-block__head {
    flex-direction: column;
  }

  .section-block__actions {
    width: 100%;
  }

  .section-block--panel {
    padding: 1rem;
  }
}
</style>
