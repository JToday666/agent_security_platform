<template>
  <article class="metric-stat">
    <p class="metric-stat__label">{{ label }}</p>
    <strong class="metric-stat__value">{{ value }}</strong>
    <p v-if="description" class="metric-stat__description">{{ description }}</p>
  </article>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    label: string;
    value: string;
    description?: string;
  }>(),
  {
    description: "",
  },
);
</script>

<style scoped lang="scss">
.metric-stat {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
  padding: 0.15rem 0;
}

.metric-stat__label {
  margin: 0;
  color: var(--color-text-subtle);
  font-size: 0.82rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  text-transform: uppercase;
}

.metric-stat__value {
  display: block;
  color: var(--color-text-dark);
  font-size: clamp(1.42rem, 2.8vw, 2.1rem);
  line-height: 1.02;
  letter-spacing: -0.04em;
}

.metric-stat__description {
  margin: 0;
  color: var(--color-text-muted);
  font-size: 0.9rem;
  line-height: 1.65;
}
</style>
