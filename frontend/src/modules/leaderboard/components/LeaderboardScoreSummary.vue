<template>
  <dl class="leaderboard-score-summary">
    <div>
      <dt>{{ t("leaderboard.overview.listedAgents") }}</dt>
      <dd>{{ entryCount }}</dd>
    </div>
    <div>
      <dt>{{ t("leaderboard.overview.currentSecurityCapability") }}</dt>
      <dd>{{ formatLeaderboardScore(champion?.safeCapabilityScore, t) }}</dd>
    </div>
    <div>
      <dt>{{ t("leaderboard.overview.lowestRiskScore") }}</dt>
      <dd>{{ formatLeaderboardScore(bestRiskScore, t) }}</dd>
    </div>
  </dl>
</template>

<script setup lang="ts">
import { useI18n } from "vue-i18n";
import { formatLeaderboardScore } from "@/modules/leaderboard/lib/leaderboard-view";
import type { LeaderboardEntry } from "@/modules/leaderboard/types/leaderboard-types";

defineProps<{
  entryCount: number;
  champion: LeaderboardEntry | null;
  bestRiskScore: number | null;
}>();

const { t } = useI18n();
</script>

<style scoped lang="scss">
.leaderboard-score-summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin: 0;
  border-left: 1px solid rgba(148, 163, 184, 0.16);
}

.leaderboard-score-summary div {
  display: flex;
  min-width: 0;
  flex-direction: column;
  justify-content: center;
  padding: 1.45rem 1.1rem;
  border-left: 1px solid rgba(148, 163, 184, 0.12);
}

.leaderboard-score-summary div:first-child {
  border-left: 0;
}

.leaderboard-score-summary dt {
  color: var(--color-text-subtle);
  font-size: 0.78rem;
  font-weight: 800;
}

.leaderboard-score-summary dd {
  margin: 0.45rem 0 0;
  color: var(--color-text-dark);
  font-size: 1.55rem;
  font-variant-numeric: tabular-nums;
  font-weight: 900;
}

@media (max-width: 1024px) {
  .leaderboard-score-summary {
    grid-template-columns: 1fr;
    border-left: 0;
    border-top: 1px solid rgba(148, 163, 184, 0.16);
  }

  .leaderboard-score-summary div {
    border-left: 0;
    border-top: 1px solid rgba(148, 163, 184, 0.12);
  }

  .leaderboard-score-summary div:first-child {
    border-top: 0;
  }
}

@media (max-width: 768px) {
  .leaderboard-score-summary div {
    padding: 1.1rem 0.85rem;
  }
}
</style>
