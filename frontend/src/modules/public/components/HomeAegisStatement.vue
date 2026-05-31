<template>
  <div class="aegis-statement">
    <span class="aegis-statement__eyebrow">
      {{ t("public.home.sections.aegis.nameLabel") }}
    </span>
    <strong class="aegis-statement__title">AEGIS</strong>
    <p class="aegis-statement__expansion">{{ section.expansion }}</p>
    <p class="aegis-statement__lead">{{ section.description }}</p>
    <div class="aegis-statement__story-grid">
      <p
        v-for="storyLine in section.story"
        :key="storyLine"
        class="aegis-statement__story"
      >
        {{ storyLine }}
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from "vue-i18n";
import type { HomeInfoSection } from "@/modules/public/model/home-page-types";

defineProps<{
  section: HomeInfoSection;
}>();

const { t } = useI18n();
</script>

<style scoped lang="scss">
.aegis-statement {
  position: relative;
  display: flex;
  min-width: 0;
  max-width: 66rem;
  flex-direction: column;
  align-items: center;
  gap: 0.72rem;
  margin-inline: auto;
  padding: 0.6rem 0 0.35rem;
  isolation: isolate;
  text-align: center;
}

.aegis-statement::before {
  content: "";
  position: absolute;
  inset: -1.3rem 8% auto;
  z-index: -1;
  height: 13rem;
  background: radial-gradient(
    50% 66% at 50% 10%,
    rgba(37, 99, 235, 0.13),
    rgba(14, 165, 233, 0.06) 48%,
    transparent 76%
  );
  pointer-events: none;
}

.aegis-statement__eyebrow {
  color: var(--color-primary);
  font-size: 0.86rem;
  font-weight: 850;
  line-height: 1.35;
  overflow-wrap: anywhere;
}

.aegis-statement__title {
  max-width: 100%;
  color: var(--color-text-dark);
  font-size: 5rem;
  font-weight: 880;
  line-height: 0.98;
  letter-spacing: 0;
  overflow-wrap: anywhere;
}

.aegis-statement__expansion {
  max-width: min(58rem, 100%);
  margin: 0;
  color: rgba(51, 65, 85, 0.92);
  font-size: 1.18rem;
  font-weight: 720;
  line-height: 1.55;
  overflow-wrap: anywhere;
}

.aegis-statement__lead {
  max-width: min(62rem, 100%);
  margin: 0.12rem 0 0;
  color: var(--color-text-dark);
  font-size: 1.12rem;
  font-weight: 740;
  line-height: 1.68;
  overflow-wrap: anywhere;
}

.aegis-statement__story-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1.1rem;
  width: min(58rem, 100%);
  min-width: 0;
  margin-top: 0.5rem;
}

.aegis-statement__story {
  min-width: 0;
  margin: 0;
  color: var(--color-text-muted);
  font-size: 1.02rem;
  line-height: 1.78;
  overflow-wrap: anywhere;
}

@media (max-width: 1080px) {
  .aegis-statement__title {
    font-size: 4rem;
  }
}

@media (max-width: 768px) {
  .aegis-statement {
    gap: 0.58rem;
    padding-top: 0.3rem;
  }

  .aegis-statement::before {
    inset-inline: 0;
    height: 10rem;
  }

  .aegis-statement__title {
    font-size: 3rem;
  }

  .aegis-statement__expansion {
    max-width: 34rem;
    font-size: 1.02rem;
    line-height: 1.58;
  }

  .aegis-statement__lead {
    max-width: 36rem;
    font-size: 1.02rem;
    line-height: 1.68;
  }

  .aegis-statement__story-grid {
    grid-template-columns: 1fr;
    gap: 0.7rem;
    width: min(36rem, 100%);
    margin-top: 0.35rem;
  }

  .aegis-statement__story {
    font-size: 0.98rem;
    line-height: 1.72;
  }
}

@media (max-width: 420px) {
  .aegis-statement__title {
    font-size: 2.6rem;
  }
}
</style>
