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
  gap: 0.75rem;
  margin-bottom: 2rem; /* 增加整体的呼吸感 */
}

.page-hero__eyebrow {
  display: inline-flex;
  align-items: center;
  width: fit-content;
  margin: 0 0 0.25rem 0;
  padding: 0.35rem 0.85rem;
  background: var(--glass-bg-90); /* 加入半透明质感 */
  border: 1px solid rgba(99, 102, 241, 0.22);
  border-radius: var(--radius-pill);
  box-shadow: 0 4px 12px -4px rgba(99, 102, 241, 0.12); /* 悬浮科技感 */
  color: #4338ca;
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.06em;
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
  font-size: clamp(2rem, 4vw, 3rem); /* 随屏幕弹性的现代大厂字体流 */
  font-weight: 800;
  line-height: 1.1;
  letter-spacing: -0.02em;
  text-wrap: balance;
  overflow: visible;
}

.page-hero__title.ui-title-gradient {
  text-shadow: 0 8px 18px rgba(99, 102, 241, 0.1);
}

.page-hero__description {
  margin: 0.85rem 0 0;
  max-width: 58ch;
  color: var(--color-text-muted);
  font-size: 1.08rem; /* 增大说明文案字号增加对比和易读性 */
  line-height: 1.75;
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
