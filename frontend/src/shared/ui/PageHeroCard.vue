<template>
  <section class="hero-card ui-surface-glass" :class="`hero-card--${density}`">
    <p v-if="eyebrow" class="eyebrow">{{ eyebrow }}</p>
    <div class="hero-top">
      <div class="copy">
        <h1 class="hero-title">{{ title }}</h1>
        <p class="hero-description">{{ description }}</p>
      </div>
      <div v-if="$slots.actions" class="actions">
        <slot name="actions" />
      </div>
    </div>

    <div
      v-if="chips.length"
      class="hero-chip-grid grid-auto-fit"
    >
      <div v-for="chip in chips" :key="chip.label" class="chip ui-surface-white">
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
    description: string;
    chips?: HeroChip[];
    density?: "default" | "compact";
  }>(),
  {
    eyebrow: "",
    chips: () => [],
    density: "compact",
  },
);
</script>

<style scoped>
.hero-card {
  position: relative;
  overflow: hidden;
  border-radius: 1.9rem;
  padding: 1.5rem 1.6rem;
  margin-bottom: 1.15rem;
}

.hero-card::before,
.hero-card::after {
  content: "";
  position: absolute;
  border-radius: 999px;
  pointer-events: none;
}

.hero-card::before {
  top: -96px;
  right: -84px;
  width: 180px;
  height: 180px;
  background: radial-gradient(circle, rgba(59, 130, 246, 0.18), transparent 70%);
}

.hero-card::after {
  bottom: -132px;
  left: -108px;
  width: 220px;
  height: 220px;
  background: radial-gradient(circle, rgba(124, 58, 237, 0.16), transparent 72%);
}

.eyebrow {
  position: relative;
  z-index: 1;
  margin: 0 0 0.55rem;
  color: #2563eb;
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 0.1em;
}

.hero-top {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1.5rem;
}

.copy {
  max-width: 700px;
}

.hero-title {
  margin: 0;
  font-size: 2.2rem;
  font-weight: 800;
  line-height: 1.08;
  text-wrap: balance;
}

.hero-description {
  margin: 0.7rem 0 0;
  color: #475569;
  font-size: 0.95rem;
  line-height: 1.65;
  max-width: 58ch;
}

.actions {
  flex-shrink: 0;
}

.hero-chip-grid {
  --grid-min-size: 150px;
  --grid-gap: 0.8rem;
  position: relative;
  z-index: 1;
  margin-top: 1.1rem;
}

.chip {
  border-radius: 1rem;
  padding: 0.82rem 0.95rem;
  backdrop-filter: blur(2px);
}

.chip-label {
  display: block;
  color: #64748b;
  font-size: 0.8rem;
  margin-bottom: 0.28rem;
}

.chip-value {
  color: #0f172a;
  font-size: 1.02rem;
  font-weight: 700;
}

.hero-card--default {
  border-radius: 2.4rem;
  padding: 2.4rem;
  margin-bottom: 1.8rem;
}

.hero-card--default::before {
  top: -80px;
  right: -60px;
  width: 240px;
  height: 240px;
}

.hero-card--default::after {
  bottom: -120px;
  left: -90px;
  width: 280px;
  height: 280px;
}

.hero-card--default .eyebrow {
  margin-bottom: 0.8rem;
  font-size: 0.92rem;
  letter-spacing: 0.08em;
}

.hero-card--default .copy {
  max-width: 760px;
}

.hero-card--default .hero-title {
  font-size: 3rem;
  line-height: 1.1;
}

.hero-card--default .hero-description {
  margin-top: 1rem;
  font-size: 1.05rem;
  line-height: 1.8;
  max-width: 60ch;
}

.hero-card--default .hero-chip-grid {
  --grid-min-size: 180px;
  --grid-gap: 1rem;
  margin-top: 1.8rem;
}

.hero-card--default .chip {
  border-radius: 1.2rem;
  padding: 1rem 1.1rem;
}

.hero-card--default .chip-label {
  font-size: 0.88rem;
  margin-bottom: 0.4rem;
}

.hero-card--default .chip-value {
  font-size: 1.2rem;
}

@media (max-width: 1024px) {
  .hero-card {
    padding: 1.3rem 1.35rem;
    border-radius: 1.65rem;
  }

  .hero-title {
    font-size: 1.95rem;
  }

  .hero-card--default {
    padding: 2rem;
    border-radius: 2rem;
  }

  .hero-card--default .hero-title {
    font-size: 2.6rem;
  }
}

@media (max-width: 768px) {
  .hero-card {
    padding: 1.2rem;
    border-radius: 1.35rem;
  }

  .hero-top {
    flex-direction: column;
    gap: 0.95rem;
  }

  .actions {
    width: 100%;
  }

  .actions :deep(a),
  .actions :deep(button) {
    width: 100%;
    justify-content: center;
  }

  .hero-title {
    font-size: 1.72rem;
  }

  .hero-description {
    max-width: none;
    font-size: 0.92rem;
  }

  .hero-card--default {
    padding: 1.45rem;
    border-radius: 1.6rem;
  }

  .hero-card--default .hero-title {
    font-size: 2rem;
  }

  .hero-card--default .hero-description {
    font-size: 0.98rem;
  }
}
</style>
