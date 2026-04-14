<template>
  <label :class="['form-field', { full, 'form-field-textarea': type === 'textarea' }]">
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
      <span v-if="leadingIcon" class="form-field__icon" aria-hidden="true">
        <AppIcon :icon="leadingIcon" />
      </span>
      <select
        v-if="type === 'select'"
        :value="modelValue"
        :disabled="disabled"
        class="form-field-input"
        @change="$emit('update:modelValue', ($event.target as HTMLSelectElement).value)"
      >
        <option v-for="option in options" :key="option.value" :value="option.value">
          {{ option.label }}
        </option>
      </select>
      <textarea
        v-else-if="type === 'textarea'"
        :value="modelValue"
        :placeholder="placeholder"
        :rows="rows"
        :disabled="disabled"
        :readonly="readonly"
        :autocomplete="autocomplete || undefined"
        class="form-field-input"
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
        class="form-field-input"
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
  options?: Array<{
    label: string;
    value: string;
  }>;
}

const props = withDefaults(defineProps<Props>(), {
  type: 'text',
  full: false,
  disabled: false,
  rows: 4,
  required: false,
  readonly: false,
  autocomplete: "",
  leadingIcon: "",
  hint: "",
  options: () => [],
});

defineEmits<{
  (e: 'update:modelValue', value: string): void;
}>();

const resolvedHelp = computed(() => props.help || props.hint);
</script>

<style scoped lang="scss">
.form-field {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
}

.form-field.full {
  grid-column: 1 / -1;
}

.form-field-label {
  color: #334155;
  font-weight: 600;
  font-size: 0.95rem;
}

.form-field-control {
  position: relative;
}

.form-field-control--with-icon .form-field-input {
  padding-left: 2.8rem;
}

.form-field__icon {
  position: absolute;
  left: 0.95rem;
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
  padding: 0.82rem 1rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.75rem;
  background: #ffffff;
  color: #0f172a;
  font-family: inherit;
  font-size: 0.95rem;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.form-field-input:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.form-field-input:disabled {
  background-color: #f1f5f9;
  color: #94a3b8;
  cursor: not-allowed;
}

.form-field-input[readonly] {
  background-color: #f8fafc;
  color: #64748b;
}

.form-field-textarea .form-field-input {
  resize: vertical;
  min-height: 120px;
  border-radius: 1.2rem;
}

.form-field-error {
  color: #dc2626;
  font-size: 0.875rem;
}

.form-field-help {
  color: #64748b;
  font-size: 0.875rem;
}

@media (max-width: 768px) {
  .form-field {
    grid-column: 1 / -1;
  }
}
</style>
