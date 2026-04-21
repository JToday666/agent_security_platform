<template>
  <label class="ui-toggle-field">
    <div class="ui-toggle-field__copy">
      <strong class="ui-toggle-field__title">{{ title }}</strong>
      <p v-if="description" class="ui-toggle-field__description">{{ description }}</p>
    </div>

    <input
      :checked="modelValue"
      :disabled="disabled"
      type="checkbox"
      class="ui-toggle-field__input"
      @change="$emit('update:modelValue', ($event.target as HTMLInputElement).checked)"
    />
  </label>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    modelValue: boolean;
    title: string;
    description?: string;
    disabled?: boolean;
  }>(),
  {
    description: "",
    disabled: false,
  },
);

defineEmits<{
  (event: "update:modelValue", value: boolean): void;
}>();
</script>

<style scoped lang="scss">
.ui-toggle-field {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 1rem 0;
  border-top: 1px solid rgba(148, 163, 184, 0.16);
}

.ui-toggle-field__copy {
  min-width: 0;
}

.ui-toggle-field__title {
  display: block;
  color: var(--color-text-dark);
}

.ui-toggle-field__description {
  margin: 0.35rem 0 0;
  color: var(--color-text-subtle);
  line-height: 1.65;
}

.ui-toggle-field__input {
  appearance: none;
  width: 46px;
  height: 28px;
  flex-shrink: 0;
  border-radius: 999px;
  border: 1px solid rgba(148, 163, 184, 0.24);
  background: rgba(226, 232, 240, 0.92);
  position: relative;
  cursor: pointer;
  transition:
    background var(--duration-fast) var(--ease-standard),
    border-color var(--duration-fast) var(--ease-standard),
    box-shadow var(--duration-fast) var(--ease-standard);
}

.ui-toggle-field__input::after {
  content: "";
  position: absolute;
  top: 3px;
  left: 3px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #ffffff;
  box-shadow: 0 8px 18px -12px rgba(15, 23, 42, 0.28);
  transition: transform var(--duration-fast) var(--ease-standard);
}

.ui-toggle-field__input:checked {
  background: linear-gradient(135deg, #3b82f6, #6366f1);
  border-color: rgba(79, 70, 229, 0.3);
}

.ui-toggle-field__input:checked::after {
  transform: translateX(18px);
}

.ui-toggle-field__input:focus-visible {
  outline: none;
  box-shadow: var(--shadow-focus-primary);
}

.ui-toggle-field__input:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

@media (max-width: 768px) {
  .ui-toggle-field {
    align-items: flex-start;
  }
}
</style>
