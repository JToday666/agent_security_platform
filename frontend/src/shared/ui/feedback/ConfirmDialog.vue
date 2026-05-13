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
            <div v-if="showIcon" class="icon-wrapper">
              <AppIcon icon="app:status.warning" class="icon" />
            </div>

            <h3 v-if="titleText" class="confirm-title">{{ titleText }}</h3>
            <p class="confirm-message">{{ message }}</p>

            <div class="button-group">
              <UiButton
                v-if="showCancel"
                variant="secondary"
                :disabled="loading"
                @click="handleCancel"
              >
                {{ cancelText || t("common.actions.cancel") }}
              </UiButton>
              <UiButton
                :variant="danger ? 'danger' : 'primary'"
                :loading="loading"
                @click="handleConfirm"
              >
                {{ confirmText || t("common.actions.confirm") }}
              </UiButton>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import AppIcon from "../branding/AppIcon.vue";
import UiButton from "../actions/UiButton.vue";

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
  showCancel: true,
  danger: false,
  showIcon: true,
  loading: false,
});

const { t } = useI18n();
const titleText = computed(() => props.title ?? t("common.dialog.title"));

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

const afterLeave = () => {};
</script>

<style scoped lang="scss">
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
  min-width: 0;
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
  overflow-wrap: anywhere;
}

.confirm-message {
  font-size: 1rem;
  color: #475569;
  margin: 0 0 2rem;
  line-height: 1.5;
  overflow-wrap: anywhere;
  white-space: pre-line;
}

.button-group {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: center;
  min-width: 0;
}

.button-group :deep(.ui-button) {
  flex: 1 1 min(12rem, 100%);
  min-width: 0;
}
</style>
