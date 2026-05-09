<template>
  <div class="ui-select" ref="containerRef">
    <button
      class="ui-select__trigger"
      :class="[
        `ui-select__trigger--${size}`,
        {
          'is-open': isOpen,
          'is-disabled': disabled,
          'ui-select__trigger--with-icon': Boolean(leadingIcon),
        },
      ]"
      type="button"
      :disabled="disabled"
      :aria-expanded="isOpen ? 'true' : 'false'"
      @click="toggle"
      @keydown.esc.prevent="close"
    >
      <span v-if="leadingIcon" class="ui-select__leading-icon" aria-hidden="true">
        <AppIcon :icon="leadingIcon" />
      </span>
      <span
        class="ui-select__label"
        :class="{ 'ui-select__label--placeholder': !hasSelectedLabel }"
      >
        {{ selectedLabel }}
      </span>
      <span class="ui-select__suffix" aria-hidden="true">
        <AppIcon
          icon="lucide:chevrons-up-down"
          class="ui-select__icon"
          :class="{ 'is-open': isOpen }"
        />
      </span>
    </button>

    <Transition name="fade-slide-y">
      <div v-show="isOpen" class="ui-select__dropdown ui-surface-glass">
        <ul class="ui-select__list" role="listbox">
          <li
            v-for="option in props.options"
            :key="String(option.value)"
            class="ui-select__item"
            :class="{ 'is-selected': isSelected(option.value) }"
            role="option"
            :aria-selected="isSelected(option.value)"
            @click="selectOption(option.value)"
          >
            <span class="ui-select__item-label">{{ option.label }}</span>
            <AppIcon
              v-if="isSelected(option.value)"
              icon="lucide:check"
              class="ui-select__item-icon"
            />
          </li>
        </ul>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import AppIcon from "../branding/AppIcon.vue";

interface Option {
  label: string;
  value: string | number;
}

const props = withDefaults(
  defineProps<{
    modelValue: string | number;
    options: Option[];
    placeholder?: string;
    disabled?: boolean;
    leadingIcon?: string;
    size?: "sm" | "md";
  }>(),
  {
    placeholder: "请选择",
    disabled: false,
    leadingIcon: "",
    size: "md",
  },
);

const emit = defineEmits<{
  (e: "update:modelValue", value: string | number): void;
}>();

const isOpen = ref(false);
const containerRef = ref<HTMLElement | null>(null);

const selectedLabel = computed(() => {
  const selected = props.options.find((opt) => opt.value === props.modelValue);
  return selected ? selected.label : props.placeholder;
});

const hasSelectedLabel = computed(() =>
  props.options.some((opt) => opt.value === props.modelValue),
);

const isSelected = (val: string | number) => val === props.modelValue;

const toggle = () => {
  if (props.disabled) {
    return;
  }

  isOpen.value = !isOpen.value;
};

const close = () => {
  isOpen.value = false;
};

const selectOption = (val: string | number) => {
  emit("update:modelValue", val);
  close();
};

const handleClickOutside = (event: MouseEvent) => {
  if (containerRef.value && !containerRef.value.contains(event.target as Node)) {
    close();
  }
};

onMounted(() => {
  document.addEventListener("mousedown", handleClickOutside);
});

onUnmounted(() => {
  document.removeEventListener("mousedown", handleClickOutside);
});
</script>

<style scoped lang="scss">
.ui-select {
  position: relative;
  width: 100%;
  min-width: 0;
}

.ui-select__trigger {
  width: 100%;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 0.7rem;
  justify-content: space-between;
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: var(--radius-input);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.94), rgba(248, 250, 252, 0.92));
  color: var(--color-text-dark);
  cursor: pointer;
  box-shadow: 0 10px 20px -22px rgba(15, 23, 42, 0.28);
  transition:
    border-color var(--duration-fast) var(--ease-standard),
    box-shadow var(--duration-fast) var(--ease-standard),
    background var(--duration-fast) var(--ease-standard),
    transform var(--duration-fast) var(--ease-standard);
}

.ui-select__trigger--md {
  min-height: 3rem;
  padding: 0.82rem 0.95rem;
}

.ui-select__trigger--sm {
  min-height: 2.65rem;
  padding: 0.66rem 0.86rem;
  border-radius: 1rem;
}

.ui-select__trigger:hover:not(.is-disabled) {
  border-color: rgba(99, 102, 241, 0.22);
  box-shadow: 0 14px 26px -24px rgba(79, 70, 229, 0.28);
}

.ui-select__trigger.is-open {
  border-color: rgba(79, 70, 229, 0.36);
  box-shadow: var(--shadow-focus-primary);
}

.ui-select__trigger.is-disabled {
  background: rgba(241, 245, 249, 0.9);
  color: #94a3b8;
  cursor: not-allowed;
  opacity: 0.8;
}

.ui-select__leading-icon,
.ui-select__suffix {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.ui-select__leading-icon {
  width: 1.1rem;
  color: var(--color-text-subtle);
}

.ui-select__label {
  flex: 1;
  min-width: 0;
  font-size: 0.92rem;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  text-align: left;
}

.ui-select__label--placeholder {
  color: var(--color-text-subtle);
  font-weight: 500;
}

.ui-select__icon {
  width: 1rem;
  height: 1rem;
  color: var(--color-text-muted);
  transition: transform var(--duration-base) var(--ease-standard);
}

.ui-select__icon.is-open {
  transform: rotate(180deg);
}

.ui-select__dropdown {
  position: absolute;
  top: calc(100% + 0.45rem);
  left: 0;
  width: 100%;
  min-width: min(100%, 14rem);
  z-index: var(--z-modal, 2000);
  border-radius: 1.1rem;
  padding: 0.45rem;
  border: 1px solid rgba(148, 163, 184, 0.18);
  box-shadow: 0 22px 42px -32px rgba(15, 23, 42, 0.3);
}

.ui-select__list {
  list-style: none;
  margin: 0;
  padding: 0;
  max-height: 240px;
  overflow-y: auto;
}

.ui-select__list::-webkit-scrollbar {
  width: 4px;
}

.ui-select__list::-webkit-scrollbar-thumb {
  background-color: rgba(148, 163, 184, 0.34);
  border-radius: 4px;
}

.ui-select__item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.8rem;
  padding: 0.7rem 0.8rem;
  margin-bottom: 2px;
  border-radius: 0.9rem;
  cursor: pointer;
  transition:
    background var(--duration-fast) var(--ease-standard),
    color var(--duration-fast) var(--ease-standard);
}

.ui-select__item:last-child {
  margin-bottom: 0;
}

.ui-select__item:hover {
  background: rgba(59, 130, 246, 0.08);
}

.ui-select__item.is-selected {
  background: linear-gradient(135deg, rgba(219, 234, 254, 0.88), rgba(237, 233, 254, 0.82));
  color: var(--color-primary-hover);
  font-weight: 600;
}

.ui-select__item-label {
  font-size: 0.9rem;
  overflow-wrap: anywhere;
}

.ui-select__item-icon {
  width: 0.95rem;
  height: 0.95rem;
  color: var(--color-primary);
}

@media (max-width: 768px) {
  .ui-select__dropdown {
    position: static;
    margin-top: 0.55rem;
  }
}
</style>
