<template>
  <div class="content leaderboard-page layout-page-shell layout-page-shell--wide">
    <PageHero
      :title="t('leaderboard.page.title')"
      :description="t('leaderboard.page.description')"
      align="center"
    />

    <PageStatePanel
      v-if="loading && !snapshot"
      :title="t('leaderboard.page.loadingTitle')"
      :message="t('common.feedback.pleaseWait')"
      :loading="true"
    />

    <PageStatePanel
      v-else-if="error && !snapshot"
      :title="errorTitle"
      :message="error"
      :action-text="t('common.actions.retry')"
      @action="loadLeaderboard"
    />

    <template v-else-if="snapshot && hasEntries">
      <section class="leaderboard-hero" :aria-label="t('leaderboard.overview.aria')">
        <LeaderboardChampionPanel
          :entry="champion"
          :sort-state="sortState"
        />
        <LeaderboardScoreSummary
          :entry-count="snapshot.entryCount"
          :champion="champion"
          :best-risk-score="bestRiskScore"
        />
      </section>

      <section class="leaderboard-table-section" aria-labelledby="leaderboard-title">
        <div class="section-head">
          <div>
            <h2 id="leaderboard-title">{{ t("leaderboard.table.title") }}</h2>
            <p>
              {{ t("leaderboard.table.description", { sort: activeSortOption.label }) }}
            </p>
          </div>
        </div>

        <LeaderboardTable
          :entries="sortedEntries"
          :sort-state="sortState"
          @sort-change="handleSortChange"
        />
      </section>
    </template>

    <PageStatePanel
      v-else
      :title="t('leaderboard.empty.title')"
      :message="t('leaderboard.empty.message')"
    >
      <UiButton
        :to="RouteLocation.datasetList"
        variant="primary"
        leading-icon="app:action.browseDataset"
      >
        {{ t("common.actions.browseDataset") }}
      </UiButton>
    </PageStatePanel>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { useI18n } from "vue-i18n";
import { RouteLocation } from "@/app/router/route-names";
import LeaderboardChampionPanel from "@/modules/leaderboard/components/LeaderboardChampionPanel.vue";
import LeaderboardScoreSummary from "@/modules/leaderboard/components/LeaderboardScoreSummary.vue";
import LeaderboardTable from "@/modules/leaderboard/components/LeaderboardTable.vue";
import { useLeaderboardPage } from "@/modules/leaderboard/composables/useLeaderboardPage";
import {
  DEFAULT_LEADERBOARD_SORT,
  getLeaderboardSortOption,
  getNextLeaderboardSortState,
  sortLeaderboardEntries,
  type LeaderboardSortKey,
  type LeaderboardSortState,
} from "@/modules/leaderboard/lib/leaderboard-view";
import UiButton from "@/shared/ui/actions/UiButton.vue";
import PageStatePanel from "@/shared/ui/feedback/PageStatePanel.vue";
import PageHero from "@/shared/ui/page/PageHero.vue";

const { t } = useI18n();

const {
  snapshot,
  entries,
  hasEntries,
  loading,
  error,
  errorTitle,
  loadLeaderboard,
} = useLeaderboardPage();

const sortState = ref<LeaderboardSortState>({ ...DEFAULT_LEADERBOARD_SORT });

const sortedEntries = computed(() =>
  sortLeaderboardEntries(entries.value, sortState.value),
);

const champion = computed(() => sortedEntries.value[0] ?? null);

const bestRiskScore = computed(() => {
  if (!entries.value.length) {
    return null;
  }

  return Math.min(...entries.value.map((entry) => entry.unsafeRiskScore));
});

const activeSortOption = computed(() =>
  getLeaderboardSortOption(sortState.value.key, t),
);

const handleSortChange = (key: LeaderboardSortKey) => {
  sortState.value = getNextLeaderboardSortState(sortState.value, key);
};
</script>

<style scoped lang="scss">
.leaderboard-page {
  padding-bottom: 2.6rem;
}

.leaderboard-hero {
  display: grid;
  grid-template-columns: minmax(260px, 0.9fr) minmax(0, 1.4fr);
  gap: 1.2rem;
  align-items: stretch;
  min-width: 0;
  margin-bottom: 1.35rem;
  border-top: 1px solid rgba(148, 163, 184, 0.18);
  border-bottom: 1px solid rgba(148, 163, 184, 0.16);
  background:
    linear-gradient(135deg, rgba(219, 234, 254, 0.42), transparent 38%),
    linear-gradient(135deg, rgba(255, 255, 255, 0.78), rgba(248, 250, 252, 0.5));
}

.leaderboard-table-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  min-width: 0;
  padding-top: 1.25rem;
  border-top: 1px solid rgba(148, 163, 184, 0.18);
}

.section-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  min-width: 0;
}

.section-head h2 {
  margin: 0;
  color: var(--color-text-dark);
  font-size: 1.18rem;
}

.section-head p {
  margin: 0.4rem 0 0;
  max-width: 68ch;
  color: var(--color-text-subtle);
  line-height: 1.68;
  overflow-wrap: anywhere;
}

@media (max-width: 1024px) {
  .leaderboard-hero {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .leaderboard-page {
    padding-bottom: 1.8rem;
  }

  .section-head {
    flex-direction: column;
  }
}
</style>
