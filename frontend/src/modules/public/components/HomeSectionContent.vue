<template>
  <div
    class="home-section-content"
    :class="`home-section-content--${section.key}`"
  >
    <HomeAegisStatement v-if="section.kind === 'aegis'" :section="section" />

    <div v-else class="product-section__layout">
      <div class="section-context">
        <p>{{ section.description }}</p>
      </div>

      <div v-if="section.kind === 'loop'" class="loop-panel">
        <article
          v-for="(item, index) in section.items"
          :key="item.key"
          class="loop-step"
        >
          <span class="loop-step__index">
            {{ formatSectionStep(index) }}
          </span>
          <span class="loop-step__icon">
            <AppIcon :icon="item.icon" />
          </span>
          <div class="loop-step__copy">
            <h3>{{ item.title }}</h3>
            <p>{{ item.description }}</p>
          </div>
        </article>
      </div>

      <div v-else-if="section.kind === 'trust'" class="trust-layout">
        <div class="trust-trace">
          <article
            v-for="item in section.items"
            :key="item.key"
            class="trust-trace__item"
          >
            <span class="trust-trace__icon">
              <AppIcon :icon="item.icon" />
            </span>
            <h3>{{ item.title }}</h3>
            <p>{{ item.description }}</p>
          </article>
        </div>

        <HomeLeaderboardPreview
          :entries="leaderboardEntries"
          :loading="leaderboardLoading"
          :unavailable="leaderboardUnavailable"
        />
      </div>

      <div v-else class="product-grid" :class="`product-grid--${section.key}`">
        <article
          v-for="item in section.items"
          :key="item.key"
          class="product-card"
        >
          <span class="product-card__icon">
            <AppIcon :icon="item.icon" />
          </span>
          <h3>{{ item.title }}</h3>
          <p>{{ item.description }}</p>
          <UiButton
            v-if="item.to && item.actionLabel"
            :to="item.to"
            variant="text"
            size="sm"
          >
            {{ item.actionLabel }}
          </UiButton>
        </article>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { LeaderboardEntry } from "@/modules/leaderboard/types/leaderboard-types";
import HomeAegisStatement from "@/modules/public/components/HomeAegisStatement.vue";
import HomeLeaderboardPreview from "@/modules/public/components/HomeLeaderboardPreview.vue";
import type { HomeInfoSection } from "@/modules/public/model/home-page-types";
import UiButton from "@/shared/ui/actions/UiButton.vue";
import AppIcon from "@/shared/ui/branding/AppIcon.vue";

defineProps<{
  section: HomeInfoSection;
  leaderboardEntries: LeaderboardEntry[];
  leaderboardLoading: boolean;
  leaderboardUnavailable: boolean;
}>();

const formatSectionStep = (index: number): string =>
  String(index + 1).padStart(2, "0");
</script>

<style scoped lang="scss">
.home-section-content {
  min-width: 0;
}

.product-section__layout {
  display: grid;
  grid-template-columns: minmax(0, 0.82fr) minmax(0, 1.18fr);
  align-items: center;
  gap: 1.75rem;
  min-width: 0;
}

.section-context {
  min-width: 0;
  max-width: 34rem;
}

.section-context p {
  margin: 0;
  color: var(--color-text-muted);
  font-size: 1.04rem;
  line-height: 1.72;
  overflow-wrap: anywhere;
}

.product-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
  min-width: 0;
}

.product-card {
  position: relative;
  display: flex;
  min-width: 0;
  min-height: 12.4rem;
  flex-direction: column;
  gap: 0.75rem;
  padding: 1.15rem;
  overflow: hidden;
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: var(--radius-control-sm);
  background: rgba(255, 255, 255, 0.76);
  box-shadow: var(--shadow-surface-soft);
  transition:
    border-color var(--duration-fast) var(--ease-standard),
    box-shadow var(--duration-fast) var(--ease-standard),
    transform var(--duration-fast) var(--ease-standard);
}

.product-card::before {
  content: "";
  position: absolute;
  inset: 0 auto 0 0;
  width: 3px;
  background: linear-gradient(
    180deg,
    rgba(37, 99, 235, 0.66),
    rgba(14, 165, 233, 0.26)
  );
}

.product-card:hover {
  border-color: rgba(37, 99, 235, 0.28);
  box-shadow: var(--shadow-surface-hover);
  transform: translateY(-1px);
}

.product-card__icon,
.loop-step__icon,
.trust-trace__icon {
  display: inline-flex;
  width: 2.35rem;
  height: 2.35rem;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(37, 99, 235, 0.16);
  border-radius: var(--radius-control-sm);
  background: rgba(219, 234, 254, 0.5);
  color: var(--color-primary);
}

.home-section-content--experience .product-card__icon {
  border-color: rgba(14, 165, 233, 0.22);
  background: rgba(207, 250, 254, 0.58);
  color: #0e7490;
}

.product-card h3 {
  margin: 0;
  color: var(--color-text-dark);
  font-size: 1.04rem;
  line-height: 1.42;
  overflow-wrap: anywhere;
}

.product-card p {
  margin: 0;
  flex: 1;
  color: var(--color-text-muted);
  line-height: 1.7;
  overflow-wrap: anywhere;
}

.product-card :deep(.ui-button) {
  align-self: flex-start;
}

.loop-panel {
  display: grid;
  min-width: 0;
  overflow: hidden;
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: var(--radius-control-sm);
  background: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.82),
    rgba(239, 246, 255, 0.72)
  );
  box-shadow: var(--shadow-surface-mid);
}

.loop-step {
  display: grid;
  grid-template-columns: auto auto minmax(0, 1fr);
  align-items: start;
  gap: 0.9rem;
  min-width: 0;
  padding: 1.15rem;
  border-top: 1px solid rgba(148, 163, 184, 0.18);
}

.loop-step:first-child {
  border-top: 0;
}

.loop-step__index {
  color: rgba(37, 99, 235, 0.68);
  font-family: var(
    --font-mono,
    ui-monospace,
    SFMono-Regular,
    Menlo,
    Monaco,
    Consolas,
    monospace
  );
  font-size: 0.84rem;
  font-weight: 800;
  line-height: 2.35rem;
}

.loop-step__icon {
  border-color: rgba(14, 165, 233, 0.22);
  background: rgba(207, 250, 254, 0.46);
  color: #0369a1;
}

.loop-step__copy {
  min-width: 0;
}

.loop-step__copy h3,
.trust-trace__item h3 {
  margin: 0;
  color: var(--color-text-dark);
  font-size: 1.04rem;
  line-height: 1.42;
  overflow-wrap: anywhere;
}

.loop-step__copy p,
.trust-trace__item p {
  margin: 0.45rem 0 0;
  color: var(--color-text-muted);
  line-height: 1.7;
  overflow-wrap: anywhere;
}

.trust-layout {
  display: grid;
  grid-template-columns: minmax(0, 0.92fr) minmax(280px, 0.78fr);
  gap: 1rem;
  min-width: 0;
}

.trust-trace {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.85rem;
  min-width: 0;
}

.trust-trace__item {
  position: relative;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 0.75rem 0.9rem;
  min-width: 0;
  padding: 1rem;
  border: 1px solid rgba(5, 150, 105, 0.16);
  border-radius: var(--radius-control-sm);
  background: rgba(255, 255, 255, 0.74);
}

.trust-trace__item h3 {
  align-self: center;
}

.trust-trace__item p {
  grid-column: 2;
}

.trust-trace__icon {
  border-color: rgba(5, 150, 105, 0.18);
  background: rgba(209, 250, 229, 0.52);
  color: #047857;
}

@media (max-width: 1080px) {
  .product-section__layout {
    grid-template-columns: 1fr;
  }

  .section-context {
    max-width: 58rem;
  }

  .trust-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .product-section__layout {
    gap: 1rem;
  }

  .product-grid {
    grid-template-columns: 1fr;
  }

  .section-context p {
    font-size: 1rem;
  }

  .loop-step {
    grid-template-columns: auto minmax(0, 1fr);
  }

  .loop-step__index {
    grid-row: span 2;
  }

  .loop-step__icon {
    display: none;
  }

  .trust-trace__item {
    grid-template-columns: 1fr;
  }

  .trust-trace__item p {
    grid-column: auto;
  }

  .product-card {
    min-height: auto;
  }
}
</style>
