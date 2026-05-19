<template>
  <button
    :id="id"
    class="home-section-jump"
    :class="`home-section-jump--${variant}`"
    type="button"
    :aria-label="jumpAriaLabel"
    :aria-controls="controls"
    @click="$emit('activate')"
    @mousemove="handleGlow"
    @focus="handleGlow"
  >
    <span class="home-section-jump__title">
      {{ title }}
    </span>
    <span class="home-section-jump__description">
      {{ description }}
    </span>
  </button>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    id: string;
    title: string;
    description: string;
    controls: string;
    jumpAriaLabel: string;
    variant?: "hero" | "between";
  }>(),
  {
    variant: "between",
  },
);

defineEmits<{
  activate: [];
}>();

const handleGlow = (event: MouseEvent | FocusEvent) => {
  const target = event.currentTarget as HTMLElement | null;

  if (!target) {
    return;
  }

  const rect = target.getBoundingClientRect();
  const x =
    event instanceof MouseEvent ? event.clientX - rect.left : rect.width / 2;
  const y =
    event instanceof MouseEvent ? event.clientY - rect.top : rect.height / 2;

  target.style.setProperty("--jump-x", `${x}px`);
  target.style.setProperty("--jump-y", `${y}px`);
};
</script>

<style scoped lang="scss">
.home-section-jump {
  --jump-x: 50%;
  --jump-y: 50%;
  position: relative;
  z-index: 1;
  display: flex;
  width: min(50rem, 100%);
  min-width: 0;
  min-height: 6.6rem;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.46rem;
  margin-inline: auto;
  padding: 1.1rem 1rem;
  overflow: hidden;
  border: 0;
  background: transparent;
  color: inherit;
  cursor: pointer;
  font: inherit;
  scroll-margin-top: calc(var(--nav-height) + 1rem);
  text-align: center;
  transition:
    color var(--duration-fast) var(--ease-standard),
    transform var(--duration-fast) var(--ease-standard);
}

.home-section-jump--hero {
  margin-top: 1.35rem;
}

.home-section-jump--between {
  margin-top: 2.1rem;
}

.home-section-jump::after {
  content: "";
  position: absolute;
  inset: 0;
  background: radial-gradient(
    420px circle at var(--jump-x) var(--jump-y),
    rgba(59, 130, 246, 0.13),
    rgba(14, 165, 233, 0.07) 38%,
    transparent 72%
  );
  opacity: 0.7;
  pointer-events: none;
  transition: opacity var(--duration-fast) var(--ease-standard);
}

.home-section-jump:hover,
.home-section-jump:focus-visible {
  transform: translateY(-1px);
}

.home-section-jump:hover::after,
.home-section-jump:focus-visible::after {
  opacity: 1;
}

.home-section-jump:focus-visible {
  outline: 3px solid rgba(37, 99, 235, 0.2);
  outline-offset: 0.35rem;
}

.home-section-jump__title,
.home-section-jump__description {
  position: relative;
  z-index: 1;
}

.home-section-jump__title {
  max-width: 100%;
  color: var(--color-primary);
  font-size: 2.12rem;
  font-weight: 820;
  letter-spacing: 0;
  line-height: 1.16;
  overflow-wrap: anywhere;
  transition: color var(--duration-fast) var(--ease-standard);
}

.home-section-jump__description {
  max-width: min(48rem, 100%);
  color: rgba(71, 85, 105, 0.92);
  font-size: 0.96rem;
  line-height: 1.55;
  overflow-wrap: anywhere;
  transition: color var(--duration-fast) var(--ease-standard);
}

.home-section-jump:hover .home-section-jump__title,
.home-section-jump:focus-visible .home-section-jump__title {
  color: var(--color-primary-hover);
}

.home-section-jump:hover .home-section-jump__description,
.home-section-jump:focus-visible .home-section-jump__description {
  color: var(--color-text-dark);
}

@media (max-width: 768px) {
  .home-section-jump {
    width: 100%;
    min-height: 5.4rem;
    padding: 0.95rem 0.75rem;
  }

  .home-section-jump--between {
    margin-top: 1.5rem;
  }

  .home-section-jump__title {
    font-size: 1.62rem;
  }

  .home-section-jump__description {
    font-size: 0.94rem;
  }
}
</style>
