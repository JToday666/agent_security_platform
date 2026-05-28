<template>
  <div
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
    <label
      v-if="label"
      :id="labelId"
      class="form-field-label"
      :for="controlId"
    >
      {{ label }}
      <span v-if="required" class="required-mark">*</span>
    </label>

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
        :id="controlId"
        :model-value="modelValue"
        :options="options"
        :disabled="disabled"
        :placeholder="placeholder"
        :leading-icon="leadingIcon"
        :size="size"
        :label-id="labelId || undefined"
        :described-by="describedBy"
        :invalid="isInvalid"
        @update:model-value="$emit('update:modelValue', String($event))"
      />

      <textarea
        v-else-if="type === 'textarea'"
        :id="controlId"
        :value="textInputValue"
        :placeholder="placeholder"
        :rows="rows"
        :disabled="disabled"
        :readonly="readonly"
        :autocomplete="autocomplete || undefined"
        :aria-describedby="describedBy"
        :aria-invalid="isInvalid ? 'true' : undefined"
        :class="['form-field-input', size === 'sm' ? 'form-field-input--sm' : '']"
        @focus="handleFocus"
        @input="handleTextInput"
        @blur="handleBlur"
      />

      <input
        v-else
        :id="controlId"
        :type="type"
        :value="textInputValue"
        :placeholder="placeholder"
        :disabled="disabled"
        :readonly="readonly"
        :autocomplete="autocomplete || undefined"
        :aria-describedby="describedBy"
        :aria-invalid="isInvalid ? 'true' : undefined"
        :class="['form-field-input', size === 'sm' ? 'form-field-input--sm' : '']"
        @focus="handleFocus"
        @input="handleTextInput"
        @blur="handleBlur"
      />
    </div>

    <small v-if="error" :id="errorId" class="form-field-error">{{ error }}</small>
    <small v-else-if="resolvedHelp" :id="helpId" class="form-field-help">
      {{ resolvedHelp }}
    </small>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, useId, watch } from "vue";
import AppIcon from "../branding/AppIcon.vue";
import type { AppIconName } from "../branding/app-icon-registry";
import UiSelect from "./UiSelect.vue";

interface Props {
  id?: string;
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
  leadingIcon?: AppIconName | "";
  appearance?: "line" | "soft";
  size?: "sm" | "md";
  updateOnBlur?: boolean;
  options?: Array<{
    label: string;
    value: string;
  }>;
}

const props = withDefaults(defineProps<Props>(), {
  id: "",
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
  updateOnBlur: false,
  hint: "",
  options: () => [],
});

const emit = defineEmits<{
  (e: "update:modelValue", value: string): void;
}>();

const fieldId = useId();
const draftValue = ref(props.modelValue);
const isEditing = ref(false);
const resolvedHelp = computed(() => props.help || props.hint);
const isSelect = computed(() => props.type === "select");
const controlId = computed(() => props.id || `${fieldId}-control`);
const labelId = computed(() =>
  props.label ? `${controlId.value}-label` : "",
);
const errorId = computed(() =>
  props.error ? `${controlId.value}-error` : "",
);
const helpId = computed(() =>
  resolvedHelp.value ? `${controlId.value}-help` : "",
);
const describedBy = computed(() =>
  props.error
    ? errorId.value
    : resolvedHelp.value
      ? helpId.value
      : undefined,
);
const isInvalid = computed(() => Boolean(props.error));
const textInputValue = computed(() =>
  props.updateOnBlur ? draftValue.value : props.modelValue,
);

watch(
  () => props.modelValue,
  (value) => {
    if (!props.updateOnBlur || !isEditing.value) {
      draftValue.value = value;
    }
  },
);

const getInputValue = (event: Event): string =>
  (event.target as HTMLInputElement | HTMLTextAreaElement).value;

const handleFocus = () => {
  if (props.updateOnBlur) {
    isEditing.value = true;
  }
};

const handleTextInput = (event: Event) => {
  const value = getInputValue(event);
  if (props.updateOnBlur) {
    draftValue.value = value;
    return;
  }
  emit("update:modelValue", value);
};

const handleBlur = () => {
  if (!props.updateOnBlur) {
    return;
  }
  isEditing.value = false;
  emit("update:modelValue", draftValue.value);
  void nextTick(() => {
    if (!isEditing.value) {
      draftValue.value = props.modelValue;
    }
  });
};
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
