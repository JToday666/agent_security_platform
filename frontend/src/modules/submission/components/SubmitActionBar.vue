<template>
  <section class="action-card ui-surface-glass">
    <div v-if="errorMessage || syncMessage" class="status-list">
      <p v-if="syncMessage" class="status-message sync">{{ syncMessage }}</p>
      <p v-if="errorMessage" class="status-message error">{{ errorMessage }}</p>
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
        {{ submitting ? "提交中..." : "提交任务" }}
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
    errorMessage?: string;
    syncMessage?: string;
  }>(),
  {
    errorMessage: "",
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

.status-message.sync {
  background: rgba(255, 237, 213, 0.9);
  color: #c2410c;
}

.status-message.error {
  background: rgba(254, 226, 226, 0.9);
  color: #b91c1c;
}

.action-row {
  display: flex;
  justify-content: flex-end;
  gap: 0.8rem;
}

.status-list + .action-row {
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
