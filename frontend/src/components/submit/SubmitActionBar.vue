<template>
  <section class="action-card ui-surface-glass">
    <div class="status-list">
      <p v-if="restoreMessage" class="status-message restore">{{ restoreMessage }}</p>
      <p v-if="syncMessage" class="status-message sync">{{ syncMessage }}</p>
      <p v-if="errorMessage" class="status-message error">{{ errorMessage }}</p>
      <p v-for="warning in warnings" :key="warning" class="status-message warning">
        {{ warning }}
      </p>
    </div>

    <div class="action-row">
      <button class="secondary-btn ui-btn ui-btn-pill" type="button" @click="$emit('reset')">
        重置当前页
      </button>
      <button
        class="primary-btn ui-btn ui-btn-pill ui-btn-gradient ui-btn-hover-lift"
        type="submit"
        :disabled="submitting || !canSubmit"
      >
        {{ submitting ? "提交中..." : "预检查并提交" }}
      </button>
    </div>
  </section>
</template>

<script setup lang="ts">
defineEmits<{
  (event: "reset"): void;
}>();

withDefaults(
  defineProps<{
    submitting: boolean;
    canSubmit: boolean;
    warnings?: string[];
    errorMessage?: string;
    restoreMessage?: string;
    syncMessage?: string;
  }>(),
  {
    warnings: () => [],
    errorMessage: "",
    restoreMessage: "",
    syncMessage: "",
  },
);
</script>

<style scoped>
.action-card {
  border-radius: 1.8rem;
  padding: 1.3rem;
}

.status-list {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
}

.status-message {
  margin: 0;
  padding: 0.9rem 1rem;
  border-radius: 1rem;
  font-weight: 600;
}

.status-message.restore {
  background: rgba(219, 234, 254, 0.9);
  color: #1d4ed8;
}

.status-message.sync {
  background: rgba(255, 237, 213, 0.9);
  color: #c2410c;
}

.status-message.error {
  background: rgba(254, 226, 226, 0.9);
  color: #b91c1c;
}

.status-message.warning {
  background: rgba(240, 253, 244, 0.92);
  color: #15803d;
}

.action-row {
  display: flex;
  justify-content: flex-end;
  gap: 0.8rem;
  margin-top: 1rem;
}

.secondary-btn {
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid #cbd5e1;
  color: #334155;
  padding: 0.82rem 1.1rem;
}

.primary-btn {
  padding: 0.82rem 1.3rem;
  border: none;
}

.primary-btn:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .action-row {
    flex-direction: column;
  }
}
</style>
