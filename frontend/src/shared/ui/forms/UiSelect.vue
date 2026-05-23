<template>
  <div class="ui-select" ref="containerRef">
    <button
      :id="triggerId"
      ref="triggerRef"
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
      aria-haspopup="listbox"
      :aria-expanded="isOpen ? 'true' : 'false'"
      :aria-controls="listboxId"
      :aria-labelledby="triggerLabelledBy"
      :aria-describedby="describedBy || undefined"
      :aria-invalid="invalid ? 'true' : undefined"
      @click="toggle"
      @keydown="handleTriggerKeydown"
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
          icon="app:control.selectToggle"
          class="ui-select__icon"
          :class="{ 'is-open': isOpen }"
        />
      </span>
    </button>

    <Transition name="fade-slide-y">
      <div v-show="isOpen" class="ui-select__dropdown ui-surface-glass">
        <ul
          :id="listboxId"
          ref="listboxRef"
          class="ui-select__list"
          role="listbox"
          tabindex="-1"
          :aria-labelledby="triggerId"
          :aria-activedescendant="activeDescendant"
          @keydown="handleListboxKeydown"
        >
          <li
            v-for="(option, index) in props.options"
            :key="String(option.value)"
            :id="optionIds[index]"
            class="ui-select__item"
            :class="{
              'is-active': index === activeIndex,
              'is-selected': isSelected(option.value),
            }"
            role="option"
            :aria-selected="isSelected(option.value)"
            @pointerdown.prevent
            @click.stop="selectOption(option.value)"
            @mouseenter="setActiveIndex(index)"
          >
            <span class="ui-select__item-label">{{ option.label }}</span>
            <AppIcon
              v-if="isSelected(option.value)"
              icon="app:action.select"
              class="ui-select__item-icon"
            />
          </li>
        </ul>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, useId } from "vue";
import { useI18n } from "vue-i18n";
import AppIcon from "../branding/AppIcon.vue";
import type { AppIconName } from "../branding/app-icon-registry";

interface Option {
  label: string;
  value: string | number;
}

const props = withDefaults(
  defineProps<{
    modelValue: string | number;
    options: Option[];
    id?: string;
    placeholder?: string;
    disabled?: boolean;
    leadingIcon?: AppIconName | "";
    size?: "sm" | "md";
    labelId?: string;
    describedBy?: string;
    invalid?: boolean;
  }>(),
  {
    id: "",
    placeholder: "",
    disabled: false,
    leadingIcon: "",
    size: "md",
    labelId: "",
    describedBy: "",
    invalid: false,
  },
);

const { t } = useI18n();
const emit = defineEmits<{
  (e: "update:modelValue", value: string | number): void;
}>();

const TYPEAHEAD_TIMEOUT_MS = 500;

const selectId = useId();
const isOpen = ref(false);
const activeIndex = ref(-1);
const containerRef = ref<HTMLElement | null>(null);
const triggerRef = ref<HTMLButtonElement | null>(null);
const listboxRef = ref<HTMLUListElement | null>(null);
const typeaheadBuffer = ref("");
let typeaheadTimer: number | null = null;

const triggerId = computed(() => props.id || `${selectId}-trigger`);
const listboxId = computed(() => `${selectId}-listbox`);
const triggerLabelledBy = computed(() =>
  props.labelId ? `${props.labelId} ${triggerId.value}` : triggerId.value,
);

const selectedLabel = computed(() => {
  const selected = props.options.find((opt) => opt.value === props.modelValue);
  return selected
    ? selected.label
    : props.placeholder || t("common.forms.selectPlaceholder");
});

const hasSelectedLabel = computed(() =>
  props.options.some((opt) => opt.value === props.modelValue),
);

const isSelected = (val: string | number) => val === props.modelValue;

const selectedIndex = computed(() =>
  props.options.findIndex((option) => option.value === props.modelValue),
);

const optionIds = computed(() =>
  props.options.map((_, index) => `${selectId}-option-${index}`),
);

const activeDescendant = computed(() =>
  isOpen.value && activeIndex.value >= 0
    ? optionIds.value[activeIndex.value]
    : undefined,
);

const normalizeIndex = (index: number) => {
  const optionCount = props.options.length;

  if (!optionCount) {
    return -1;
  }

  return ((index % optionCount) + optionCount) % optionCount;
};

const getInitialActiveIndex = (fallbackIndex = 0) =>
  selectedIndex.value >= 0 ? selectedIndex.value : fallbackIndex;

const clearTypeahead = () => {
  typeaheadBuffer.value = "";

  if (typeaheadTimer) {
    window.clearTimeout(typeaheadTimer);
    typeaheadTimer = null;
  }
};

const scheduleTypeaheadReset = () => {
  if (typeaheadTimer) {
    window.clearTimeout(typeaheadTimer);
  }

  typeaheadTimer = window.setTimeout(() => {
    typeaheadBuffer.value = "";
    typeaheadTimer = null;
  }, TYPEAHEAD_TIMEOUT_MS);
};

const focusListbox = () => {
  void nextTick(() => {
    listboxRef.value?.focus();
  });
};

const setActiveIndex = (index: number) => {
  activeIndex.value = normalizeIndex(index);
};

const openListbox = (preferredIndex = getInitialActiveIndex()) => {
  if (props.disabled || !props.options.length) {
    return;
  }

  setActiveIndex(preferredIndex);
  isOpen.value = true;
  focusListbox();
};

const close = (restoreFocus = false) => {
  isOpen.value = false;
  activeIndex.value = -1;
  clearTypeahead();

  if (restoreFocus) {
    triggerRef.value?.focus();
  }
};

const toggle = () => {
  if (props.disabled) {
    return;
  }

  if (isOpen.value) {
    close(true);
    return;
  }

  openListbox();
};

const selectOption = (val: string | number) => {
  emit("update:modelValue", val);
  close(true);
};

const selectActiveOption = () => {
  const activeOption = props.options[activeIndex.value];

  if (activeOption) {
    selectOption(activeOption.value);
  }
};

const moveActiveOption = (offset: number) => {
  if (!props.options.length) {
    return;
  }

  setActiveIndex(activeIndex.value < 0 ? getInitialActiveIndex() : activeIndex.value + offset);
};

const setBoundaryActiveOption = (position: "first" | "last") => {
  if (!props.options.length) {
    return;
  }

  setActiveIndex(position === "first" ? 0 : props.options.length - 1);
};

const normalizeTypeaheadValue = (value: string) =>
  value.trim().toLocaleLowerCase();

const findTypeaheadIndex = (query: string) => {
  const normalizedQuery = normalizeTypeaheadValue(query);

  if (!normalizedQuery || !props.options.length) {
    return -1;
  }

  const startIndex = activeIndex.value >= 0 ? activeIndex.value + 1 : 0;

  for (let offset = 0; offset < props.options.length; offset += 1) {
    const index = normalizeIndex(startIndex + offset);
    const label = normalizeTypeaheadValue(props.options[index]?.label ?? "");

    if (label.startsWith(normalizedQuery)) {
      return index;
    }
  }

  return -1;
};

const handleTypeaheadKey = (event: KeyboardEvent) => {
  if (
    event.key.length !== 1 ||
    event.key === " " ||
    event.altKey ||
    event.ctrlKey ||
    event.metaKey
  ) {
    return false;
  }

  const nextBuffer = `${typeaheadBuffer.value}${event.key}`;
  let nextIndex = findTypeaheadIndex(nextBuffer);

  if (nextIndex < 0 && typeaheadBuffer.value) {
    nextIndex = findTypeaheadIndex(event.key);
    typeaheadBuffer.value = event.key;
  } else {
    typeaheadBuffer.value = nextBuffer;
  }

  if (nextIndex >= 0) {
    event.preventDefault();
    setActiveIndex(nextIndex);
  }

  scheduleTypeaheadReset();
  return nextIndex >= 0;
};

const handleTriggerKeydown = (event: KeyboardEvent) => {
  if (props.disabled) {
    return;
  }

  switch (event.key) {
    case "ArrowDown":
      event.preventDefault();
      if (isOpen.value) {
        moveActiveOption(1);
      } else {
        openListbox(getInitialActiveIndex(0));
      }
      break;
    case "ArrowUp":
      event.preventDefault();
      if (isOpen.value) {
        moveActiveOption(-1);
      } else {
        openListbox(
          selectedIndex.value >= 0 ? selectedIndex.value : props.options.length - 1,
        );
      }
      break;
    case "Enter":
    case " ":
      event.preventDefault();
      if (isOpen.value) {
        selectActiveOption();
      } else {
        openListbox();
      }
      break;
    case "Escape":
      if (isOpen.value) {
        event.preventDefault();
        close(true);
      }
      break;
    default:
      if (isOpen.value) {
        handleTypeaheadKey(event);
      }
  }
};

const handleListboxKeydown = (event: KeyboardEvent) => {
  switch (event.key) {
    case "ArrowDown":
      event.preventDefault();
      moveActiveOption(1);
      break;
    case "ArrowUp":
      event.preventDefault();
      moveActiveOption(-1);
      break;
    case "Home":
      event.preventDefault();
      setBoundaryActiveOption("first");
      break;
    case "End":
      event.preventDefault();
      setBoundaryActiveOption("last");
      break;
    case "Enter":
    case " ":
      event.preventDefault();
      selectActiveOption();
      break;
    case "Escape":
      event.preventDefault();
      close(true);
      break;
    case "Tab":
      close();
      break;
    default:
      handleTypeaheadKey(event);
  }
};

const handleClickOutside = (event: MouseEvent) => {
  if (containerRef.value && !containerRef.value.contains(event.target as Node)) {
    close();
  }
};

onMounted(() => {
  document.addEventListener("pointerdown", handleClickOutside);
});

onUnmounted(() => {
  document.removeEventListener("pointerdown", handleClickOutside);
  clearTypeahead();
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
  touch-action: manipulation;
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

.ui-select__trigger:focus-visible {
  outline: none;
  border-color: rgba(79, 70, 229, 0.42);
  box-shadow: var(--shadow-focus-primary);
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
  max-height: min(260px, calc(100vh - 8rem));
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
  max-height: min(240px, calc(100vh - 9rem));
  overflow-y: auto;
  overscroll-behavior: contain;
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
  min-width: 0;
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

.ui-select__item:hover,
.ui-select__item.is-active {
  background: rgba(59, 130, 246, 0.08);
}

.ui-select__item.is-selected {
  background: linear-gradient(135deg, rgba(219, 234, 254, 0.88), rgba(237, 233, 254, 0.82));
  color: var(--color-primary-hover);
  font-weight: 600;
}

.ui-select__item-label {
  min-width: 0;
  font-size: 0.9rem;
  overflow-wrap: anywhere;
}

.ui-select__item-icon {
  width: 0.95rem;
  height: 0.95rem;
  flex: 0 0 auto;
  color: var(--color-primary);
}

@media (max-width: 768px) {
  .ui-select__dropdown {
    top: calc(100% + 0.38rem);
    border-radius: 1rem;
  }
}
</style>
