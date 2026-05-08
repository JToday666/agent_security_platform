<template>
  <header class="page-hero" :class="`page-hero--align-${align}`">
    <p v-if="eyebrow" class="page-hero__eyebrow">{{ eyebrow }}</p>

    <div class="page-hero__top">
      <div v-if="$slots.prefix" class="page-hero__prefix">
        <slot name="prefix" />
      </div>

      <div class="page-hero__copy">
        <h1 class="page-hero__title ui-title-gradient">{{ title }}</h1>
        <p
          v-if="description"
          class="page-hero__description"
          :class="{
            'page-hero__description--single-line':
              descriptionWrap === 'single-line',
          }"
        >
          {{ description }}
        </p>
      </div>

      <div v-if="$slots.actions" class="page-hero__actions">
        <slot name="actions" />
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    eyebrow?: string;
    title: string;
    description?: string;
    align?: "start" | "center";
    descriptionWrap?: "balance" | "single-line";
  }>(),
  {
    eyebrow: "",
    description: "",
    align: "start",
    descriptionWrap: "balance",
  },
);
</script>

<style scoped lang="scss">
.page-hero {
  display: flex;
  flex-direction: column;
  gap: 0.55rem;
  margin-bottom: 1.2rem;
}

.page-hero__eyebrow {
  display: inline-flex;
  align-items: center;
  width: fit-content;
  margin: 0;
  color: #4f46e5;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.page-hero__top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1.1rem;
}

.page-hero__prefix {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.page-hero__copy {
  min-width: 0;
  max-width: 56rem;
  padding-block: 0.05rem;
}

.page-hero__title {
  margin: 0;
  padding-block: 0.08em 0.12em;
  display: block;
  font-size: 2.8rem;
  font-weight: 800;
  line-height: 1.08;
  letter-spacing: 0;
  text-wrap: balance;
  overflow: visible;
}

.page-hero__title.ui-title-gradient {
  text-shadow: 0 8px 18px rgba(99, 102, 241, 0.1);
}

.page-hero__description {
  margin: 0.68rem 0 0;
  max-width: 56ch;
  color: var(--color-text-muted);
  font-size: 1rem;
  line-height: 1.7;
  text-wrap: balance;
}

.page-hero__description--single-line {
  max-width: none;
}

.page-hero__actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.75rem;
  flex-shrink: 0;
}

.page-hero--align-center,
.page-hero--align-center .page-hero__top {
  align-items: center;
  text-align: center;
}

.page-hero--align-center .page-hero__top {
  flex-direction: column;
  justify-content: center;
}

.page-hero--align-center .page-hero__copy,
.page-hero--align-center .page-hero__actions {
  margin-inline: auto;
  justify-content: center;
}

.page-hero--align-center .page-hero__eyebrow {
  margin-inline: auto;
}

@media (max-width: 900px) {
  .page-hero__top {
    flex-direction: column;
  }

  .page-hero__actions {
    width: 100%;
  }

  .page-hero__actions :deep(a),
  .page-hero__actions :deep(button) {
    width: 100%;
    justify-content: center;
  }
}

@media (max-width: 768px) {
  .page-hero {
    margin-bottom: 1rem;
  }

  .page-hero__title {
    font-size: 2.15rem;
  }

}
</style>
