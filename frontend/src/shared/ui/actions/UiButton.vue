<template>
  <component
    :is="componentTag"
    v-bind="componentAttrs"
    class="ui-button"
    :class="[
      `ui-button--${variant}`,
      `ui-button--${size}`,
      {
        'ui-button--block': block,
        'ui-button--disabled': isDisabled,
        'ui-button--loading': loading,
      },
    ]"
    :aria-busy="loading ? 'true' : undefined"
    @click="handleClick"
  >
    <span v-if="leadingIcon" class="ui-button__icon" aria-hidden="true">
      <AppIcon :icon="leadingIcon" />
    </span>
    <span v-if="loading" class="ui-button__spinner" aria-hidden="true"></span>
    <span class="ui-button__content">
      <slot />
    </span>
  </component>
</template>

<script setup lang="ts">
import { computed, type Component } from "vue";
import { RouterLink, type RouteLocationRaw } from "vue-router";
import AppIcon from "../branding/AppIcon.vue";
import type { AppIconName } from "../branding/app-icon-registry";

const props = withDefaults(
  defineProps<{
    variant?: "primary" | "secondary" | "ghost" | "text" | "danger";
    size?: "sm" | "md" | "lg";
    type?: "button" | "submit" | "reset";
    to?: RouteLocationRaw;
    href?: string;
    target?: string;
    rel?: string;
    disabled?: boolean;
    block?: boolean;
    leadingIcon?: AppIconName | "";
    loading?: boolean;
    as?: string | Component;
  }>(),
  {
    variant: "secondary",
    size: "md",
    type: "button",
    to: undefined,
    href: "",
    target: "",
    rel: "",
    disabled: false,
    block: false,
    leadingIcon: "",
    loading: false,
    as: undefined,
  },
);

const isDisabled = computed(() => props.disabled || props.loading);

const componentTag = computed(() => {
  if (props.as) {
    return props.as;
  }

  if (props.to) {
    return RouterLink;
  }

  return props.href ? "a" : "button";
});

const componentAttrs = computed(() => {
  if (props.to) {
    return {
      to: props.to,
      tabindex: isDisabled.value ? -1 : undefined,
      "aria-disabled": isDisabled.value ? "true" : undefined,
    };
  }

  if (props.href) {
    return {
      href: isDisabled.value ? undefined : props.href,
      target: props.target || undefined,
      rel: props.rel || (props.target === "_blank" ? "noopener noreferrer" : undefined),
      tabindex: isDisabled.value ? -1 : undefined,
      "aria-disabled": isDisabled.value ? "true" : undefined,
    };
  }

  if (props.as && props.as !== "button") {
    return {};
  }

  return {
    type: props.type,
    disabled: isDisabled.value,
  };
});

const handleClick = (event: MouseEvent) => {
  if (isDisabled.value) {
    event.preventDefault();
    event.stopPropagation();
  }
};
</script>

<style scoped lang="scss">
.ui-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  white-space: nowrap;
  flex-shrink: 0;
  max-width: 100%;
  gap: 0.45rem;
  width: fit-content;
  border: 1px solid transparent;
  border-radius: var(--radius-pill);
  font-weight: 700;
  text-decoration: none;
  cursor: pointer;
  transition:
    transform var(--duration-fast) var(--ease-standard),
    background var(--duration-fast) var(--ease-standard),
    border-color var(--duration-fast) var(--ease-standard),
    box-shadow var(--duration-fast) var(--ease-standard),
    color var(--duration-fast) var(--ease-standard);
}

.ui-button__icon,
.ui-button__spinner {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.ui-button__icon :deep(svg) {
  width: 1rem;
  height: 1rem;
}

.ui-button__spinner {
  width: 0.95rem;
  height: 0.95rem;
  border: 2px solid currentColor;
  border-right-color: transparent;
  border-radius: 50%;
  animation: ui-button-spin 0.8s linear infinite;
}

.ui-button__content {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 0;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
}

.ui-button:hover:not(.ui-button--disabled) {
  transform: translateY(-1px);
}

.ui-button:active:not(.ui-button--disabled) {
  transform: scale(0.98);
}

.ui-button--sm {
  padding: 0.54rem 0.82rem;
  font-size: 0.84rem;
}

.ui-button--md {
  padding: 0.72rem 1rem;
  font-size: 0.92rem;
}

.ui-button--lg {
  padding: 0.88rem 1.18rem;
  font-size: 0.98rem;
}

.ui-button--block {
  width: 100%;
}

.ui-button--primary {
  background: var(--grad-primary);
  color: var(--color-white);
  box-shadow: var(--shadow-primary-btn);
}

.ui-button--primary:hover:not(.ui-button--disabled) {
  box-shadow: var(--shadow-primary-btn-hover), var(--shadow-glow);
}

.ui-button--secondary {
  background: rgba(255, 255, 255, 0.72);
  border-color: rgba(148, 163, 184, 0.2);
  color: var(--color-text-main);
}

.ui-button--ghost {
  background: rgba(255, 255, 255, 0.44);
  color: var(--color-text-muted);
}

.ui-button--text {
  padding-inline: 0;
  border-color: transparent;
  background: transparent;
  color: var(--color-primary);
}

.ui-button--text:hover:not(.ui-button--disabled) {
  transform: none;
  color: var(--color-primary-hover);
}

.ui-button--danger {
  background: linear-gradient(135deg, #fb7185, #ef4444);
  color: var(--color-white);
  box-shadow: 0 14px 28px -18px rgba(239, 68, 68, 0.52);
}

.ui-button--disabled {
  opacity: 0.56;
  cursor: not-allowed;
  pointer-events: none;
}

@keyframes ui-button-spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
