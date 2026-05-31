<template>
  <aside
    class="leaderboard-preview"
    :aria-label="t('public.home.sections.trust.leaderboard.aria')"
  >
    <div class="leaderboard-preview__head">
      <div>
        <span>{{ t("public.home.sections.trust.leaderboard.kicker") }}</span>
        <h3>{{ t("public.home.sections.trust.leaderboard.title") }}</h3>
      </div>
      <UiButton :to="RouteLocation.leaderboard" variant="text" size="sm">
        {{ t("layout.nav.leaderboard") }}
      </UiButton>
    </div>

    <div v-if="loading" class="leaderboard-preview__state">
      {{ t("common.feedback.pleaseWait") }}
    </div>
    <div v-else-if="unavailable" class="leaderboard-preview__state">
      {{ t("public.home.sections.trust.leaderboard.unavailable") }}
    </div>
    <div v-else-if="entries.length" class="leaderboard-preview__list">
      <article
        v-for="entry in entries"
        :key="`${entry.rankNo}-${entry.displayName}`"
        class="leaderboard-preview__row"
      >
        <span class="leaderboard-preview__rank">
          {{
            t("public.home.sections.trust.leaderboard.rank", {
              rank: entry.rankNo,
            })
          }}
        </span>
        <span class="leaderboard-preview__name">
          {{ entry.displayName }}
        </span>
        <span class="leaderboard-preview__score">
          {{ formatScore(entry.officialConservativeScore) }}
        </span>
        <span class="leaderboard-preview__meta">
          {{
            t("public.home.sections.trust.leaderboard.meta", {
              risk: formatScore(entry.unsafeRiskScore),
              confidence: formatScore(entry.confidence),
            })
          }}
        </span>
      </article>
    </div>
    <div v-else class="leaderboard-preview__state">
      {{ t("public.home.sections.trust.leaderboard.empty") }}
    </div>
  </aside>
</template>

<script setup lang="ts">
import { useI18n } from "vue-i18n";
import { RouteLocation } from "@/app/router/route-names";
import type { LeaderboardEntry } from "@/modules/leaderboard/types/leaderboard-types";
import UiButton from "@/shared/ui/actions/UiButton.vue";

defineProps<{
  entries: LeaderboardEntry[];
  loading: boolean;
  unavailable: boolean;
}>();

const { t } = useI18n();

const formatScore = (score: number): string => score.toFixed(1);
</script>

<style scoped lang="scss">
.leaderboard-preview {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 0.85rem;
  padding: 1rem;
  border: 1px solid rgba(37, 99, 235, 0.16);
  border-radius: var(--radius-control-sm);
  background: rgba(255, 255, 255, 0.78);
  box-shadow: var(--shadow-surface-soft);
}

.leaderboard-preview__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
  min-width: 0;
}

.leaderboard-preview__head div {
  min-width: 0;
}

.leaderboard-preview__head span {
  display: block;
  color: var(--color-primary);
  font-size: 0.78rem;
  font-weight: 800;
  overflow-wrap: anywhere;
}

.leaderboard-preview__head h3 {
  margin: 0.2rem 0 0;
  color: var(--color-text-dark);
  font-size: 1.1rem;
  line-height: 1.34;
  overflow-wrap: anywhere;
}

.leaderboard-preview__list {
  display: grid;
  gap: 0.65rem;
  min-width: 0;
}

.leaderboard-preview__row {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 0.35rem 0.7rem;
  min-width: 0;
  padding: 0.78rem;
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: var(--radius-control-sm);
  background: rgba(248, 250, 252, 0.76);
}

.leaderboard-preview__rank {
  color: var(--color-primary);
  font-size: 0.78rem;
  font-weight: 850;
}

.leaderboard-preview__name {
  min-width: 0;
  color: var(--color-text-dark);
  font-weight: 760;
  overflow-wrap: anywhere;
}

.leaderboard-preview__score {
  color: #047857;
  font-weight: 850;
  font-variant-numeric: tabular-nums;
}

.leaderboard-preview__meta {
  grid-column: 2 / 4;
  color: var(--color-text-subtle);
  font-size: 0.84rem;
  line-height: 1.55;
  overflow-wrap: anywhere;
}

.leaderboard-preview__state {
  min-width: 0;
  padding: 1rem;
  border: 1px dashed rgba(148, 163, 184, 0.24);
  border-radius: var(--radius-control-sm);
  color: var(--color-text-subtle);
  line-height: 1.7;
  overflow-wrap: anywhere;
}

@media (max-width: 768px) {
  .leaderboard-preview__head,
  .leaderboard-preview__row {
    grid-template-columns: 1fr;
  }

  .leaderboard-preview__head {
    flex-direction: column;
  }

  .leaderboard-preview__score,
  .leaderboard-preview__meta {
    grid-column: auto;
  }
}
</style>
