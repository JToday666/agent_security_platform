<template>
  <article class="metric-card ui-surface-white">
    <p class="metric-label">{{ label }}</p>
    <strong class="metric-value">{{ value }}</strong>
    <p v-if="description" class="metric-description">{{ description }}</p>
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
.metric-card {
  border-radius: 1.2rem;
  padding: 1rem 1.05rem;
  border: 1px solid rgba(148, 163, 184, 0.14);
}

.metric-label {
  margin: 0;
  color: var(--color-text-subtle);
  font-size: 0.84rem;
}

.metric-value {
  display: block;
  margin-top: 0.52rem;
  color: var(--color-text-dark);
  font-size: clamp(1.35rem, 2.6vw, 1.92rem);
  line-height: 1.05;
}

.metric-description {
  margin: 0.62rem 0 0;
  color: var(--color-text-muted);
  font-size: 0.9rem;
  line-height: 1.65;
}
</style>
