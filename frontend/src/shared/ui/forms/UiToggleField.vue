<template>
  <label class="ui-toggle-field ui-surface-muted">
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
  padding: 1rem;
  border-radius: 1.2rem;
  border: 1px solid rgba(148, 163, 184, 0.14);
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
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  accent-color: #2563eb;
}

@media (max-width: 768px) {
  .ui-toggle-field {
    align-items: flex-start;
  }
}
</style>
