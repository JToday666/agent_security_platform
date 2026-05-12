<template>
  <div class="leaderboard-table-wrap">
    <table class="leaderboard-table">
      <thead>
        <tr>
          <th scope="col">{{ t("leaderboard.table.rank") }}</th>
          <th scope="col">{{ t("leaderboard.table.agent") }}</th>
          <th
            v-for="option in sortOptions"
            :key="option.key"
            scope="col"
            :aria-sort="getAriaSort(option.key)"
          >
            <button
              type="button"
              class="sort-button"
              :class="{ 'is-active': sortState.key === option.key }"
              @click="$emit('sort-change', option.key)"
            >
              {{ option.label }}
              <AppIcon
                class="sort-button__icon"
                :icon="getSortIcon(option.key)"
                aria-hidden="true"
              />
            </button>
          </th>
          <th scope="col">{{ t("leaderboard.table.confidence") }}</th>
          <th scope="col">{{ t("leaderboard.table.samples") }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="entry in entries" :key="`${entry.rankNo}:${entry.displayName}`">
          <td class="rank-cell">
            <span :class="`rank-badge rank-badge--${getLeaderboardRankTone(entry.rankNo)}`">
              {{ entry.rankNo }}
            </span>
          </td>
          <th scope="row" class="agent-cell">
            <strong :title="entry.displayName">{{ entry.displayName }}</strong>
            <small v-if="entry.anonymous">{{ t("leaderboard.table.anonymous") }}</small>
          </th>
          <td class="score-cell score-cell--primary">
            {{ formatLeaderboardScore(entry.officialConservativeScore, t) }}
          </td>
          <td class="score-cell">{{ formatLeaderboardScore(entry.safeCapabilityScore, t) }}</td>
          <td class="score-cell">{{ formatLeaderboardScore(entry.highDifficultyScore, t) }}</td>
          <td class="score-cell score-cell--risk">
            {{ formatLeaderboardScore(entry.unsafeRiskScore, t) }}
          </td>
          <td class="score-cell">{{ formatLeaderboardScore(entry.confidence, t) }}</td>
          <td class="sample-cell">{{ entry.totalSamples }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import AppIcon from "@/shared/ui/branding/AppIcon.vue";
import {
  formatLeaderboardScore,
  getLeaderboardRankTone,
  getLeaderboardSortOptions,
  type LeaderboardSortKey,
  type LeaderboardSortState,
} from "@/modules/leaderboard/lib/leaderboard-view";
import type { LeaderboardEntry } from "@/modules/leaderboard/types/leaderboard-types";

const props = defineProps<{
  entries: LeaderboardEntry[];
  sortState: LeaderboardSortState;
}>();

const { t } = useI18n();
const sortOptions = computed(() => getLeaderboardSortOptions(t));

defineEmits<{
  (event: "sort-change", key: LeaderboardSortKey): void;
}>();

const getAriaSort = (
  key: LeaderboardSortKey,
): "ascending" | "descending" | "none" => {
  if (props.sortState.key !== key) {
    return "none";
  }

  return props.sortState.direction === "asc" ? "ascending" : "descending";
};

const getSortIcon = (key: LeaderboardSortKey): string => {
  if (props.sortState.key !== key) {
    return "app:sort.none";
  }

  return props.sortState.direction === "asc"
    ? "app:sort.ascending"
    : "app:sort.descending";
};
</script>

<style scoped lang="scss">
.leaderboard-table-wrap {
  overflow-x: auto;
  border-top: 1px solid rgba(148, 163, 184, 0.16);
}

.leaderboard-table {
  width: 100%;
  min-width: 900px;
  border-collapse: collapse;
}

.leaderboard-table th,
.leaderboard-table td {
  padding: 0.95rem 0.8rem;
  border-bottom: 1px solid rgba(148, 163, 184, 0.14);
  color: var(--color-text-muted);
  line-height: 1.45;
  text-align: left;
  vertical-align: middle;
}

.leaderboard-table thead th {
  color: var(--color-text-subtle);
  font-size: 0.78rem;
  font-weight: 850;
  white-space: nowrap;
}

.leaderboard-table tbody tr {
  transition: background var(--duration-base) var(--ease-standard);
}

.leaderboard-table tbody tr:hover {
  background: rgba(255, 255, 255, 0.72);
}

.sort-button {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0;
  border: 0;
  background: transparent;
  color: inherit;
  cursor: pointer;
  font: inherit;
  font-weight: 850;
}

.sort-button:focus-visible {
  outline: 2px solid rgba(37, 99, 235, 0.42);
  outline-offset: 4px;
}

.sort-button.is-active {
  color: var(--color-primary);
}

.sort-button__icon {
  width: 0.9rem;
  height: 0.9rem;
}

.rank-cell {
  width: 4.5rem;
}

.rank-badge {
  display: inline-flex;
  width: 2.2rem;
  height: 2.2rem;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-pill);
  background: rgba(226, 232, 240, 0.7);
  color: var(--color-text-muted);
  font-weight: 900;
}

.rank-badge--gold {
  background: linear-gradient(135deg, #fde68a, #d97706);
  color: #451a03;
}

.rank-badge--silver {
  background: linear-gradient(135deg, #e2e8f0, #64748b);
  color: #0f172a;
}

.rank-badge--bronze {
  background: linear-gradient(135deg, #fed7aa, #c2410c);
  color: #431407;
}

.agent-cell {
  min-width: 190px;
}

.agent-cell strong,
.agent-cell small {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.agent-cell strong {
  display: block;
  max-width: 220px;
  color: var(--color-text-dark);
  font-weight: 850;
}

.agent-cell small {
  display: inline-flex;
  width: fit-content;
  max-width: 220px;
  margin-top: 0.35rem;
  padding: 0.16rem 0.48rem;
  border: 1px solid rgba(37, 99, 235, 0.18);
  border-radius: 999px;
  background: rgba(37, 99, 235, 0.08);
  color: var(--color-primary);
  font-size: 0.74rem;
  font-weight: 800;
}

.score-cell,
.sample-cell {
  color: var(--color-text-dark);
  font-variant-numeric: tabular-nums;
  font-weight: 850;
  white-space: nowrap;
}

.score-cell--primary {
  color: var(--color-primary);
}

.score-cell--risk {
  color: #b91c1c;
}

</style>
