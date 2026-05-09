<template>
  <section
    class="section-block"
    :class="[
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
  }>(),
  {
    title: "",
    description: "",
    compact: false,
  },
);
</script>

<style scoped lang="scss">
.section-block {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  min-width: 0;
  padding-top: 1rem;
  border-top: 1px solid rgba(148, 163, 184, 0.16);
}

.section-block--compact {
  gap: 0.82rem;
}

.section-block__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  min-width: 0;
}

.section-block__copy {
  min-width: 0;
}

.section-block__title {
  margin: 0;
  color: var(--color-text-dark);
  font-size: 1.08rem;
  overflow-wrap: anywhere;
}

.section-block__description {
  margin: 0.35rem 0 0;
  color: var(--color-text-subtle);
  line-height: 1.68;
  overflow-wrap: anywhere;
}

.section-block__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem;
  min-width: 0;
  flex-shrink: 0;
}

.section-block__body {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  min-width: 0;
}

@media (max-width: 768px) {
  .section-block__head {
    flex-direction: column;
  }

  .section-block__actions {
    width: 100%;
  }
}
</style>
