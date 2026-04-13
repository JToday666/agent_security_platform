<template>
  <span class="ui-tag" :class="[`ui-tag--${tone}`, `ui-tag--${size}`]">
    <slot />
  </span>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    tone?:
      | "neutral"
      | "brand"
      | "info"
      | "success"
      | "warning"
      | "danger"
      | "muted";
    size?: "sm" | "md";
  }>(),
  {
    tone: "neutral",
    size: "md",
  },
);
</script>

<style scoped>
.ui-tag {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  width: fit-content;
  border: 1px solid transparent;
  border-radius: var(--radius-pill);
  font-weight: 700;
  line-height: 1.2;
}

.ui-tag--sm {
  padding: 0.26rem 0.62rem;
  font-size: 0.76rem;
}

.ui-tag--md {
  padding: 0.34rem 0.72rem;
  font-size: 0.8rem;
}

.ui-tag--neutral {
  background: rgba(226, 232, 240, 0.76);
  border-color: rgba(148, 163, 184, 0.18);
  color: var(--color-text-muted);
}

.ui-tag--brand {
  background: rgba(237, 233, 254, 0.84);
  border-color: rgba(139, 92, 246, 0.18);
  color: #6d28d9;
}

.ui-tag--info {
  background: rgba(219, 234, 254, 0.84);
  border-color: rgba(37, 99, 235, 0.18);
  color: #1d4ed8;
}

.ui-tag--success {
  background: rgba(220, 252, 231, 0.84);
  border-color: rgba(34, 197, 94, 0.2);
  color: #15803d;
}

.ui-tag--warning {
  background: rgba(254, 243, 199, 0.92);
  border-color: rgba(245, 158, 11, 0.2);
  color: #b45309;
}

.ui-tag--danger {
  background: rgba(254, 226, 226, 0.92);
  border-color: rgba(239, 68, 68, 0.2);
  color: #b91c1c;
}

.ui-tag--muted {
  background: rgba(248, 250, 252, 0.96);
  border-color: rgba(148, 163, 184, 0.16);
  color: var(--color-text-subtle);
}
</style>
