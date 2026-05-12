import { computed, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import { getLeaderboardSnapshot } from "@/modules/leaderboard/api/leaderboard-api";
import { resolveLeaderboardErrorState } from "@/modules/leaderboard/lib/leaderboard-page-state";
import type { LeaderboardSnapshot } from "@/modules/leaderboard/types/leaderboard-types";

export const useLeaderboardPage = () => {
  const { t } = useI18n();
  const snapshot = ref<LeaderboardSnapshot | null>(null);
  const loading = ref(false);
  const error = ref("");
  const errorTitle = ref(t("leaderboard.errors.loadFailedTitle"));

  const entries = computed(() => snapshot.value?.entries ?? []);
  const hasEntries = computed(() => entries.value.length > 0);

  const loadLeaderboard = async () => {
    loading.value = true;
    error.value = "";
    errorTitle.value = t("leaderboard.errors.loadFailedTitle");

    try {
      snapshot.value = await getLeaderboardSnapshot();
    } catch (loadError) {
      snapshot.value = null;
      const state = resolveLeaderboardErrorState(loadError, t);
      errorTitle.value = state.title;
      error.value = state.message;
    } finally {
      loading.value = false;
    }
  };

  onMounted(() => {
    void loadLeaderboard();
  });

  return {
    snapshot,
    entries,
    hasEntries,
    loading,
    error,
    errorTitle,
    loadLeaderboard,
  };
};
