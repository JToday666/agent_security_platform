<template>
  <section
    class="hero-card"
    :class="[
      `hero-card--${density}`,
      `hero-card--${tone}`,
      { 'hero-card--glow': glow },
    ]"
  >
    <div class="hero-backdrop" aria-hidden="true"></div>

    <p v-if="eyebrow" class="eyebrow">{{ eyebrow }}</p>

    <div class="hero-top">
      <div v-if="$slots.prefix" class="prefix">
        <slot name="prefix" />
      </div>

      <div class="copy">
        <h1
          class="hero-title"
          :class="{ 'ui-title-gradient': titleTone === 'brand' || tone === 'showcase' }"
        >
          {{ title }}
        </h1>
        <p v-if="description" class="hero-description">{{ description }}</p>
      </div>

      <div v-if="$slots.actions" class="actions">
        <slot name="actions" />
      </div>
    </div>

    <div v-if="chips.length" class="hero-chip-row">
      <div v-for="chip in chips" :key="chip.label" class="chip">
        <span class="chip-label">{{ chip.label }}</span>
        <strong class="chip-value">{{ chip.value }}</strong>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
interface HeroChip {
  label: string;
  value: string;
}

withDefaults(
  defineProps<{
    eyebrow?: string;
    title: string;
    description?: string;
    chips?: HeroChip[];
    density?: "default" | "compact";
    tone?: "showcase" | "workspace";
    titleTone?: "default" | "brand";
    glow?: boolean;
  }>(),
  {
    eyebrow: "",
    description: "",
    chips: () => [],
    density: "compact",
    tone: "workspace",
    titleTone: "default",
    glow: true,
  },
);
</script>

<style scoped>
.hero-card {
  position: relative;
  overflow: hidden;
  margin-bottom: 0.9rem;
  border-radius: 1.5rem;
  padding: 1.08rem 1.18rem;
  border: 1px solid rgba(148, 163, 184, 0.14);
}

.hero-backdrop {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.hero-card--showcase {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.84), rgba(255, 255, 255, 0.76));
  backdrop-filter: blur(var(--blur-16));
  -webkit-backdrop-filter: blur(var(--blur-16));
  box-shadow: var(--shadow-glass-card);
}

.hero-card--showcase .hero-backdrop {
  background:
    radial-gradient(circle at 0 0, rgba(59, 130, 246, 0.16), transparent 28%),
    radial-gradient(circle at 100% 0, rgba(139, 92, 246, 0.14), transparent 26%);
}

.hero-card--workspace {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.94));
  box-shadow: var(--shadow-surface-soft);
}

.hero-card--workspace .hero-backdrop {
  background:
    radial-gradient(circle at 0 0, rgba(59, 130, 246, 0.08), transparent 24%),
    radial-gradient(circle at 100% 0, rgba(99, 102, 241, 0.08), transparent 22%);
}

.hero-card--glow::after {
  content: "";
  position: absolute;
  right: -5rem;
  bottom: -7rem;
  width: 12rem;
  height: 12rem;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.72), transparent 72%);
  filter: blur(10px);
  opacity: 0.88;
  pointer-events: none;
}

.eyebrow {
  position: relative;
  z-index: 1;
  display: inline-flex;
  align-items: center;
  width: fit-content;
  margin: 0 0 0.42rem;
  padding: 0.28rem 0.62rem;
  border-radius: var(--radius-pill);
  background: rgba(255, 255, 255, 0.76);
  color: #4338ca;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.hero-top {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.85rem;
}

.prefix {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.copy {
  max-width: 720px;
}

.hero-title {
  margin: 0;
  color: var(--color-text-dark);
  font-size: clamp(1.72rem, 3.45vw, 2.56rem);
  font-weight: 800;
  line-height: 1.06;
  letter-spacing: -0.04em;
  text-wrap: balance;
}

.hero-description {
  margin: 0.58rem 0 0;
  max-width: 54ch;
  color: var(--color-text-muted);
  font-size: 0.98rem;
  line-height: 1.66;
}

.actions {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.hero-chip-row {
  position: relative;
  z-index: 1;
  display: flex;
  flex-wrap: wrap;
  gap: 0.56rem;
  margin-top: 0.82rem;
}

.chip {
  min-width: 114px;
  padding: 0.6rem 0.74rem;
  border-radius: 0.9rem;
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(148, 163, 184, 0.16);
  box-shadow: 0 12px 24px -28px rgba(15, 23, 42, 0.16);
}

.chip-label {
  display: block;
  margin-bottom: 0.16rem;
  color: var(--color-text-subtle);
  font-size: 0.72rem;
}

.chip-value {
  color: var(--color-text-dark);
  font-size: 0.95rem;
  font-weight: 700;
}

.hero-card--default {
  padding: 1.32rem;
}

@media (max-width: 900px) {
  .hero-top {
    flex-direction: column;
  }

  .prefix {
    margin-bottom: 0.2rem;
  }

  .actions {
    width: 100%;
  }

  .actions :deep(a),
  .actions :deep(button) {
    width: 100%;
    justify-content: center;
  }
}

@media (max-width: 768px) {
  .hero-card {
    border-radius: 1.3rem;
    padding: 0.96rem;
  }

  .hero-card--default {
    padding: 1.08rem;
  }
}
</style>
