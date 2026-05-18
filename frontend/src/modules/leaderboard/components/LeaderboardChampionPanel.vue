<template>
  <article class="leaderboard-champion" :aria-label="t('leaderboard.champion.aria')">
    <div class="leaderboard-champion__award" aria-hidden="true">
      <AppIcon icon="app:leaderboard.champion" />
    </div>
    <span class="leaderboard-champion__rank">No. 1</span>
    <span class="leaderboard-champion__label">{{ t("leaderboard.champion.label") }}</span>
    <strong class="leaderboard-champion__name" :title="entry?.displayName">
      {{ entry?.displayName ?? t("leaderboard.scores.notReturned") }}
    </strong>
    <span v-if="entry?.anonymous" class="leaderboard-champion__anonymous">
      {{ t("leaderboard.champion.anonymous") }}
    </span>
    <div class="leaderboard-champion__score">
      <span>{{ sortLabel }}</span>
      <strong>{{ formatLeaderboardScore(scoreValue, t) }}</strong>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import {
  formatLeaderboardScore,
  getLeaderboardSortOption,
  type LeaderboardSortState,
} from "@/modules/leaderboard/lib/leaderboard-view";
import type { LeaderboardEntry } from "@/modules/leaderboard/types/leaderboard-types";
import AppIcon from "@/shared/ui/branding/AppIcon.vue";

const props = defineProps<{
  entry: LeaderboardEntry | null;
  sortState: LeaderboardSortState;
}>();

const { t } = useI18n();
const sortLabel = computed(() =>
  getLeaderboardSortOption(props.sortState.key, t).label,
);
const scoreValue = computed(() => props.entry?.[props.sortState.key] ?? null);
</script>

<style scoped lang="scss">
.leaderboard-champion {
  position: relative;
  display: flex;
  min-width: 0;
  min-height: 15rem;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem 1.6rem;
  text-align: center;
}

.leaderboard-champion__award {
  display: inline-flex;
  width: 5rem;
  height: 5rem;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(217, 119, 6, 0.24);
  border-radius: 1.4rem;
  background:
    radial-gradient(circle at 34% 25%, rgba(254, 243, 199, 0.96), transparent 48%),
    linear-gradient(135deg, #fef3c7 0%, #f59e0b 56%, #b45309 100%);
  box-shadow:
    0 24px 44px -30px rgba(146, 64, 14, 0.82),
    0 0 0 1px rgba(255, 255, 255, 0.28) inset;
  color: #451a03;
}

.leaderboard-champion__award :deep(svg) {
  width: 2.6rem;
  height: 2.6rem;
  stroke-width: 1.8;
}

.leaderboard-champion__rank {
  margin-top: 0.62rem;
  color: #92400e;
  font-size: 0.86rem;
  font-weight: 950;
  letter-spacing: 0;
}

.leaderboard-champion__label,
.leaderboard-champion__score span {
  color: var(--color-text-subtle);
  font-size: 0.78rem;
  font-weight: 800;
}

.leaderboard-champion__name {
  display: block;
  width: 100%;
  max-width: 14ch;
  margin-top: 0.72rem;
  overflow: hidden;
  color: var(--color-text-dark);
  font-size: 2.7rem;
  font-weight: 900;
  line-height: 1.06;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.leaderboard-champion__label,
.leaderboard-champion__anonymous {
  max-width: 100%;
  overflow-wrap: anywhere;
}

.leaderboard-champion__anonymous {
  display: inline-flex;
  align-items: center;
  margin-top: 0.72rem;
  padding: 0.28rem 0.7rem;
  border: 1px solid rgba(37, 99, 235, 0.18);
  border-radius: 999px;
  background: rgba(37, 99, 235, 0.08);
  color: var(--color-primary);
  font-size: 0.78rem;
  font-weight: 850;
}

.leaderboard-champion__score {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.35rem;
  margin-top: 1.1rem;
}

.leaderboard-champion__score strong {
  color: var(--color-primary);
  font-size: 3rem;
  font-variant-numeric: tabular-nums;
  font-weight: 950;
  line-height: 1;
}

@media (max-width: 640px) {
  .leaderboard-champion {
    min-height: 12rem;
    padding: 1.55rem 1.1rem;
  }

  .leaderboard-champion__rank {
    margin-top: 0.5rem;
  }

  .leaderboard-champion__award {
    width: 4.1rem;
    height: 4.1rem;
    border-radius: 1.15rem;
  }

  .leaderboard-champion__award :deep(svg) {
    width: 2.15rem;
    height: 2.15rem;
  }

  .leaderboard-champion__name {
    font-size: 2rem;
  }

  .leaderboard-champion__score strong {
    font-size: 2.35rem;
  }
}
</style>
