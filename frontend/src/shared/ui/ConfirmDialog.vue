<template>
  <Teleport to="body">
    <Transition name="fade" @after-leave="afterLeave">
      <div
        v-if="modelValue"
        class="confirm-overlay ui-modal-overlay"
        @click.self="handleCancel"
        @keydown.esc="handleCancel"
      >
        <Transition name="scale" appear>
          <div class="confirm-card ui-modal-card">
            <div class="icon-wrapper" v-if="showIcon">
              <AppIcon icon="lucide:alert-triangle" class="icon" />
            </div>

            <h3 v-if="title" class="confirm-title">{{ title }}</h3>
            <p class="confirm-message">{{ message }}</p>

            <div class="button-group" :class="{ single: !showCancel }">
              <button
                v-if="showCancel"
                class="btn cancel ui-btn"
                @click="handleCancel"
                :disabled="loading"
              >
                {{ cancelText }}
              </button>
              <button
                class="btn confirm ui-btn ui-btn-gradient ui-btn-hover-lift"
                :class="{ danger, 'ui-btn-danger': danger }"
                @click="handleConfirm"
                :disabled="loading"
              >
                <span v-if="!loading">{{ confirmText }}</span>
                <span v-else class="loader ui-loader"></span>
              </button>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import AppIcon from "@/shared/ui/AppIcon.vue";

interface Props {
  modelValue: boolean;
  title?: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  showCancel?: boolean;
  danger?: boolean;
  showIcon?: boolean;
  loading?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  title: "提示",
  confirmText: "确认",
  cancelText: "取消",
  showCancel: true,
  danger: false,
  showIcon: true,
  loading: false,
});

const emit = defineEmits<{
  (e: "update:modelValue", value: boolean): void;
  (e: "confirm"): void;
  (e: "cancel"): void;
}>();

const close = () => {
  emit("update:modelValue", false);
};

const handleCancel = () => {
  if (props.loading) return;
  emit("cancel");
  close();
};

const handleConfirm = () => {
  if (props.loading) return;
  emit("confirm");
};

const afterLeave = () => {
};
</script>

<style scoped>
.confirm-overlay {
  background-color: var(--overlay-dark-40);
  backdrop-filter: blur(var(--blur-4));
  z-index: var(--z-modal);
}

.confirm-card {
  background: var(--glass-bg-90);
  backdrop-filter: blur(var(--blur-16));
  -webkit-backdrop-filter: blur(var(--blur-16));
  padding: 2rem 2rem 1.8rem;
  max-width: 380px;
  box-shadow:
    0 30px 60px -15px rgba(0, 0, 0, 0.3),
    0 0 0 1px rgba(255, 255, 255, 0.7) inset;
  text-align: center;
}

.icon-wrapper {
  display: flex;
  justify-content: center;
  margin-bottom: 1.2rem;
}

.icon {
  width: 48px;
  height: 48px;
  color: #f59e0b;
  filter: drop-shadow(0 4px 6px rgba(245, 158, 11, 0.2));
}

.confirm-title {
  font-size: 1.6rem;
  font-weight: 600;
  margin: 0 0 0.5rem;
  color: #0f172a;
}

.confirm-message {
  font-size: 1rem;
  color: #475569;
  margin: 0 0 2rem;
  line-height: 1.5;
  white-space: pre-line;
}

.button-group {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.button-group.single {
  grid-template-columns: 1fr;
}

.btn {
  flex: 1;
  padding: 0.8rem 1.2rem;
  border: none;
  border-radius: 40px;
  font-size: 1rem;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.02);
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.cancel {
  background: white;
  color: #64748b;
  border: 1px solid #e2e8f0;
}

.cancel:hover:not(:disabled) {
  background: #f8fafc;
  border-color: #cbd5e1;
  transform: translateY(-2px);
  box-shadow: 0 10px 20px -8px rgba(0, 0, 0, 0.1);
}

.confirm:hover:not(:disabled) {
  background: linear-gradient(135deg, #1d4ed8, #6d28d9);
}

.confirm.danger {
  background: linear-gradient(135deg, #f87171, #ef4444);
  box-shadow: 0 8px 18px -6px #ef444480;
}

.confirm.danger:hover:not(:disabled) {
  background: linear-gradient(135deg, #ef4444, #dc2626);
  box-shadow: 0 15px 25px -8px #ef4444;
}
</style>
