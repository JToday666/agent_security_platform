<template>
  <label
    :class="[
      'form-field',
      `form-field--${appearance}`,
      {
        full,
        'form-field-textarea': type === 'textarea',
        'form-field--select': isSelect,
      },
    ]"
  >
    <span v-if="label" class="form-field-label">
      {{ label }}
      <span v-if="required" class="required-mark">*</span>
    </span>

    <div
      class="form-field-control"
      :class="{
        'form-field-control--with-icon': Boolean(leadingIcon),
      }"
    >
      <span
        v-if="leadingIcon && !isSelect"
        class="form-field__icon"
        aria-hidden="true"
      >
        <AppIcon :icon="leadingIcon" />
      </span>

      <UiSelect
        v-if="isSelect"
        :model-value="modelValue"
        :options="options"
        :disabled="disabled"
        :placeholder="placeholder"
        :leading-icon="leadingIcon"
        :size="size"
        @update:model-value="$emit('update:modelValue', String($event))"
      />

      <textarea
        v-else-if="type === 'textarea'"
        :value="modelValue"
        :placeholder="placeholder"
        :rows="rows"
        :disabled="disabled"
        :readonly="readonly"
        :autocomplete="autocomplete || undefined"
        :class="['form-field-input', size === 'sm' ? 'form-field-input--sm' : '']"
        @input="$emit('update:modelValue', ($event.target as HTMLTextAreaElement).value)"
      />

      <input
        v-else
        :type="type"
        :value="modelValue"
        :placeholder="placeholder"
        :disabled="disabled"
        :readonly="readonly"
        :autocomplete="autocomplete || undefined"
        :class="['form-field-input', size === 'sm' ? 'form-field-input--sm' : '']"
        @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
      />
    </div>

    <small v-if="error" class="form-field-error">{{ error }}</small>
    <small v-else-if="resolvedHelp" class="form-field-help">{{ resolvedHelp }}</small>
  </label>
</template>

<script setup lang="ts">
import { computed } from "vue";
import AppIcon from "../branding/AppIcon.vue";
import UiSelect from "./UiSelect.vue";

interface Props {
  modelValue: string;
  label?: string;
  type?:
    | "text"
    | "email"
    | "password"
    | "url"
    | "number"
    | "textarea"
    | "search"
    | "select";
  placeholder?: string;
  error?: string;
  help?: string;
  hint?: string;
  rows?: number;
  full?: boolean;
  disabled?: boolean;
  required?: boolean;
  readonly?: boolean;
  autocomplete?: string;
  leadingIcon?: string;
  appearance?: "line" | "soft";
  size?: "sm" | "md";
  options?: Array<{
    label: string;
    value: string;
  }>;
}

const props = withDefaults(defineProps<Props>(), {
  type: "text",
  full: false,
  disabled: false,
  rows: 4,
  required: false,
  readonly: false,
  autocomplete: "",
  leadingIcon: "",
  appearance: "line",
  size: "md",
  hint: "",
  options: () => [],
});

defineEmits<{
  (e: "update:modelValue", value: string): void;
}>();

const resolvedHelp = computed(() => props.help || props.hint);
const isSelect = computed(() => props.type === "select");
</script>

<style scoped lang="scss">
.form-field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  min-width: 0;
}

.form-field.full {
  grid-column: 1 / -1;
}

.form-field-label {
  color: var(--color-text-main);
  font-weight: 600;
  font-size: 0.94rem;
  overflow-wrap: anywhere;
}

.form-field-control {
  position: relative;
  min-width: 0;
}

.form-field-control--with-icon .form-field-input {
  padding-left: 2.8rem;
}

.form-field__icon {
  position: absolute;
  left: 1rem;
  top: 50%;
  transform: translateY(-50%);
  color: #94a3b8;
  pointer-events: none;
}

.form-field__icon :deep(svg) {
  width: 1rem;
  height: 1rem;
}

.required-mark {
  color: #dc2626;
  margin-left: 0.2rem;
}

.form-field-input {
  width: 100%;
  min-width: 0;
  min-height: 3rem;
  padding: 0.88rem 1rem;
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: var(--radius-input);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.94), rgba(248, 250, 252, 0.9));
  color: var(--color-text-dark);
  font-family: inherit;
  font-size: 0.95rem;
  box-shadow: 0 10px 20px -22px rgba(15, 23, 42, 0.22);
  transition:
    border-color var(--duration-fast) var(--ease-standard),
    box-shadow var(--duration-fast) var(--ease-standard),
    background var(--duration-fast) var(--ease-standard);
}

.form-field-input:focus {
  outline: none;
  border-color: rgba(79, 70, 229, 0.42);
  background: rgba(255, 255, 255, 0.94);
  box-shadow: var(--shadow-focus-primary);
}

.form-field-input:disabled {
  background-color: rgba(241, 245, 249, 0.88);
  color: #94a3b8;
  cursor: not-allowed;
}

.form-field-input[readonly] {
  background-color: rgba(248, 250, 252, 0.92);
  color: #64748b;
}

.form-field-input--sm {
  min-height: 2.65rem;
  padding-block: 0.7rem;
  border-radius: 1rem;
  font-size: 0.9rem;
}

.form-field-textarea .form-field-input {
  resize: vertical;
  min-height: 120px;
  border-radius: 1.25rem;
}

.form-field--soft .form-field-input {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(241, 245, 249, 0.96));
}

.form-field--select :deep(.ui-select__trigger) {
  width: 100%;
}

.form-field-error {
  color: #dc2626;
  font-size: 0.875rem;
  overflow-wrap: anywhere;
}

.form-field-help {
  color: #64748b;
  font-size: 0.875rem;
  overflow-wrap: anywhere;
}

@media (max-width: 768px) {
  .form-field {
    grid-column: 1 / -1;
  }
}
</style>
