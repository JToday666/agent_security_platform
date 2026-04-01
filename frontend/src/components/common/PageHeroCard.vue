<template>
  <section class="hero-card ui-surface-glass">
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

    <div v-if="chips.length" class="chips">
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
  }>(),
  {
    eyebrow: "",
    chips: () => [],
  },
);
</script>

<style scoped>
.hero-card {
  position: relative;
  overflow: hidden;
  border-radius: 2.4rem;
  padding: 2.4rem;
  margin-bottom: 1.8rem;
}

.hero-card::before,
.hero-card::after {
  content: "";
  position: absolute;
  border-radius: 999px;
  pointer-events: none;
}

.hero-card::before {
  top: -80px;
  right: -60px;
  width: 240px;
  height: 240px;
  background: radial-gradient(circle, rgba(59, 130, 246, 0.18), transparent 70%);
}

.hero-card::after {
  bottom: -120px;
  left: -90px;
  width: 280px;
  height: 280px;
  background: radial-gradient(circle, rgba(124, 58, 237, 0.16), transparent 72%);
}

.eyebrow {
  position: relative;
  z-index: 1;
  margin: 0 0 0.8rem;
  color: #2563eb;
  font-size: 0.92rem;
  font-weight: 700;
  letter-spacing: 0.08em;
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
  max-width: 760px;
}

.hero-title {
  margin: 0;
  font-size: 3rem;
  font-weight: 800;
  line-height: 1.1;
}

.hero-description {
  margin: 1rem 0 0;
  color: #475569;
  font-size: 1.05rem;
  line-height: 1.8;
  max-width: 60ch;
}

.actions {
  flex-shrink: 0;
}

.chips {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1rem;
  margin-top: 1.8rem;
}

.chip {
  border-radius: 1.2rem;
  padding: 1rem 1.1rem;
  backdrop-filter: blur(2px);
}

.chip-label {
  display: block;
  color: #64748b;
  font-size: 0.88rem;
  margin-bottom: 0.4rem;
}

.chip-value {
  color: #0f172a;
  font-size: 1.2rem;
  font-weight: 700;
}

@media (max-width: 768px) {
  .hero-card {
    padding: 1.6rem;
    border-radius: 1.8rem;
  }

  .hero-top {
    flex-direction: column;
  }

  .hero-title {
    font-size: 2.3rem;
  }

  .hero-description {
    max-width: none;
  }
}
</style>
