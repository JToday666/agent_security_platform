import {
  translateRuntimeMessage,
  type AppTranslator,
} from "@/app/i18n/runtime-translator";
import type { LeaderboardEntry } from "@/modules/leaderboard/types/leaderboard-types";

export type LeaderboardSortKey =
  | "officialConservativeScore"
  | "safeCapabilityScore"
  | "highDifficultyScore"
  | "unsafeRiskScore";

export type LeaderboardSortDirection = "asc" | "desc";

export type LeaderboardRankTone = "gold" | "silver" | "bronze" | "base";

export interface LeaderboardSortState {
  key: LeaderboardSortKey;
  direction: LeaderboardSortDirection;
}

interface LeaderboardSortOptionBase {
  key: LeaderboardSortKey;
  labelKey: string;
  shortLabelKey: string;
  defaultDirection: LeaderboardSortDirection;
}

export interface LeaderboardSortOption {
  key: LeaderboardSortKey;
  label: string;
  shortLabel: string;
  defaultDirection: LeaderboardSortDirection;
}

const LEADERBOARD_SORT_OPTION_BASE: LeaderboardSortOptionBase[] = [
  {
    key: "officialConservativeScore",
    labelKey: "leaderboard.scores.compositeFull",
    shortLabelKey: "leaderboard.scores.composite",
    defaultDirection: "desc",
  },
  {
    key: "safeCapabilityScore",
    labelKey: "leaderboard.scores.safeCapabilityFull",
    shortLabelKey: "leaderboard.scores.safeCapability",
    defaultDirection: "desc",
  },
  {
    key: "highDifficultyScore",
    labelKey: "leaderboard.scores.highDifficultyFull",
    shortLabelKey: "leaderboard.scores.highDifficulty",
    defaultDirection: "desc",
  },
  {
    key: "unsafeRiskScore",
    labelKey: "leaderboard.scores.riskFull",
    shortLabelKey: "leaderboard.scores.risk",
    defaultDirection: "asc",
  },
];

export const DEFAULT_LEADERBOARD_SORT: LeaderboardSortState = {
  key: "officialConservativeScore",
  direction: "desc",
};

const normalizeScore = (value: number): number =>
  Number.isFinite(value) ? value : Number.NEGATIVE_INFINITY;

export const getLeaderboardSortOption = (
  key: LeaderboardSortKey,
  t: AppTranslator = translateRuntimeMessage,
): LeaderboardSortOption =>
  getLeaderboardSortOptions(t).find((option) => option.key === key) ??
  getLeaderboardSortOptions(t)[0];

export const getLeaderboardSortOptions = (
  t: AppTranslator = translateRuntimeMessage,
): LeaderboardSortOption[] =>
  LEADERBOARD_SORT_OPTION_BASE.map((option) => ({
    key: option.key,
    label: t(option.labelKey),
    shortLabel: t(option.shortLabelKey),
    defaultDirection: option.defaultDirection,
  }));

export const getNextLeaderboardSortState = (
  current: LeaderboardSortState,
  nextKey: LeaderboardSortKey,
): LeaderboardSortState => {
  if (current.key === nextKey) {
    return {
      key: nextKey,
      direction: current.direction === "desc" ? "asc" : "desc",
    };
  }

  return {
    key: nextKey,
    direction: getLeaderboardSortOption(nextKey).defaultDirection,
  };
};

export const sortLeaderboardEntries = (
  entries: LeaderboardEntry[],
  sortState: LeaderboardSortState,
): LeaderboardEntry[] => {
  const directionFactor = sortState.direction === "desc" ? -1 : 1;

  return [...entries].sort((left, right) => {
    const scoreDelta =
      normalizeScore(left[sortState.key]) -
      normalizeScore(right[sortState.key]);

    if (scoreDelta !== 0) {
      return scoreDelta * directionFactor;
    }

    return left.rankNo - right.rankNo;
  });
};

export const formatLeaderboardScore = (
  value?: number | null,
  t: AppTranslator = translateRuntimeMessage,
): string =>
  typeof value === "number" && Number.isFinite(value)
    ? value.toFixed(1)
    : t("leaderboard.scores.notReturned");

export const getLeaderboardRankTone = (rankNo: number): LeaderboardRankTone => {
  if (rankNo === 1) return "gold";
  if (rankNo === 2) return "silver";
  if (rankNo === 3) return "bronze";
  return "base";
};
