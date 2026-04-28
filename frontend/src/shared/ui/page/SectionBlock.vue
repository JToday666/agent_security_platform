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
  padding: 1.5rem;
  position: relative;
  background: linear-gradient(
    180deg,
    rgba(255, 255, 255, 0.88) 0%,
    rgba(255, 255, 255, 0.72) 100%
  );
  backdrop-filter: blur(var(--blur-12));
  -webkit-backdrop-filter: blur(var(--blur-12));
  border: 1px solid rgba(255, 255, 255, 0.9);
  border-radius: var(--radius-card-md);
  box-shadow: var(--shadow-glass-card);
  transition: transform var(--duration-base) var(--ease-standard),
              box-shadow var(--duration-base) var(--ease-standard);
}

.section-block--panel:hover {
  transform: translateY(-2px);
  box-shadow: 0 28px 56px -24px rgba(15, 23, 42, 0.18),
              0 0 0 1px rgba(255, 255, 255, 0.95) inset;
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
