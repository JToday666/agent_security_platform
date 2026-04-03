<template>
  <label :class="['form-field', { full, 'form-field-textarea': type === 'textarea' }]">
    <span v-if="label" class="form-field-label">
      {{ label }}
      <span v-if="required" class="required-mark">*</span>
    </span>
    <component
      :is="type === 'textarea' ? 'textarea' : 'input'"
      :type="type === 'textarea' ? undefined : type"
      :value="modelValue"
      :placeholder="placeholder"
      :rows="type === 'textarea' ? rows : undefined"
      :disabled="disabled"
      class="form-field-input"
      @input="$emit('update:modelValue', ($event.target as HTMLInputElement | HTMLTextAreaElement).value)"
    />
    <small v-if="error" class="form-field-error">{{ error }}</small>
    <small v-if="help" class="form-field-help">{{ help }}</small>
  </label>
</template>

<script setup lang="ts">
interface Props {
  modelValue: string;
  label?: string;
  type?: 'text' | 'email' | 'password' | 'url' | 'number' | 'textarea';
  placeholder?: string;
  error?: string;
  help?: string;
  rows?: number;
  full?: boolean;
  disabled?: boolean;
  required?: boolean;
}

withDefaults(defineProps<Props>(), {
  type: 'text',
  full: false,
  disabled: false,
  rows: 4,
  required: false,
});

defineEmits<{
  (e: 'update:modelValue', value: string): void;
}>();
</script>

<style scoped>
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
