<template>
  <article class="leaderboard-champion" aria-label="当前第一">
    <span class="leaderboard-champion__label">当前第一</span>
    <strong class="leaderboard-champion__name" :title="entry?.agentName">
      {{ entry?.agentName ?? "未返回" }}
    </strong>
    <div class="leaderboard-champion__score">
      <span>{{ sortLabel }}</span>
      <strong>{{ formatLeaderboardScore(scoreValue) }}</strong>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed } from "vue";
import {
  formatLeaderboardScore,
  getLeaderboardSortOption,
  type LeaderboardSortState,
} from "@/modules/public/lib/leaderboard-view";
import type { LeaderboardEntry } from "@/shared/types/leaderboard-types";

const props = defineProps<{
  entry: LeaderboardEntry | null;
  sortState: LeaderboardSortState;
}>();

const sortLabel = computed(() => getLeaderboardSortOption(props.sortState.key).label);
const scoreValue = computed(() => props.entry?.[props.sortState.key] ?? null);
</script>

<style scoped lang="scss">
.leaderboard-champion {
  display: flex;
  min-width: 0;
  min-height: 15rem;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 1.8rem 1.35rem;
  text-align: center;
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
  margin-top: 0.55rem;
  overflow: hidden;
  color: var(--color-text-dark);
  font-size: clamp(2rem, 5vw, 3rem);
  font-weight: 900;
  line-height: 1.06;
  text-overflow: ellipsis;
  white-space: nowrap;
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
  font-size: clamp(2.3rem, 6vw, 3.35rem);
  font-variant-numeric: tabular-nums;
  font-weight: 950;
  line-height: 1;
}
</style>
