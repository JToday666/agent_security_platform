<template>
  <div class="inline-notice" :class="`inline-notice--${tone}`">
    <div class="inline-notice-main">
      <strong v-if="title" class="inline-notice-title">{{ title }}</strong>
      <p class="inline-notice-message">
        <slot>{{ message }}</slot>
      </p>
      <div v-if="$slots.extra" class="inline-notice-extra">
        <slot name="extra" />
      </div>
    </div>

    <div v-if="$slots.actions" class="inline-notice-actions">
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    tone?: "info" | "success" | "warning" | "danger";
    title?: string;
    message?: string;
  }>(),
  {
    tone: "info",
    title: "",
    message: "",
  },
);
</script>

<style scoped lang="scss">
.inline-notice {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.9rem;
  min-width: 0;
  max-width: 100%;
  padding: 0.9rem 1rem;
  border-radius: 1rem;
  border: 1px solid transparent;
  overflow-wrap: anywhere;
}

.inline-notice-main {
  display: flex;
  min-width: 0;
  flex: 1;
  flex-direction: column;
  gap: 0.35rem;
}

.inline-notice-title {
  color: inherit;
  font-size: 0.92rem;
  overflow-wrap: anywhere;
}

.inline-notice-message {
  margin: 0;
  color: inherit;
  line-height: 1.68;
  overflow-wrap: anywhere;
}

.inline-notice-extra,
.inline-notice-actions {
  display: flex;
  min-width: 0;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.65rem;
}

.inline-notice--info {
  background: rgba(219, 234, 254, 0.84);
  border-color: rgba(37, 99, 235, 0.18);
  color: #1d4ed8;
}

.inline-notice--success {
  background: rgba(220, 252, 231, 0.84);
  border-color: rgba(34, 197, 94, 0.18);
  color: #15803d;
}

.inline-notice--warning {
  background: rgba(254, 243, 199, 0.9);
  border-color: rgba(245, 158, 11, 0.18);
  color: #b45309;
}

.inline-notice--danger {
  background: rgba(254, 226, 226, 0.9);
  border-color: rgba(239, 68, 68, 0.18);
  color: #b91c1c;
}

@media (max-width: 768px) {
  .inline-notice {
    flex-direction: column;
  }
}
</style>
