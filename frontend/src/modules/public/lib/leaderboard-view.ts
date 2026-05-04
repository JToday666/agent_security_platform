import type { LeaderboardEntry } from "@/shared/types/leaderboard-types";

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

export interface LeaderboardSortOption {
  key: LeaderboardSortKey;
  label: string;
  shortLabel: string;
  defaultDirection: LeaderboardSortDirection;
}

export interface LeaderboardCertificationView {
  tierLabel: string;
  certificationLabel: string;
  tone: "brand" | "success" | "warning" | "danger" | "muted";
}

export const LEADERBOARD_SORT_OPTIONS: LeaderboardSortOption[] = [
  {
    key: "officialConservativeScore",
    label: "综合分",
    shortLabel: "综合",
    defaultDirection: "desc",
  },
  {
    key: "safeCapabilityScore",
    label: "安全能力",
    shortLabel: "安全",
    defaultDirection: "desc",
  },
  {
    key: "highDifficultyScore",
    label: "高难分",
    shortLabel: "高难",
    defaultDirection: "desc",
  },
  {
    key: "unsafeRiskScore",
    label: "风险分",
    shortLabel: "风险",
    defaultDirection: "asc",
  },
];

export const DEFAULT_LEADERBOARD_SORT: LeaderboardSortState = {
  key: "officialConservativeScore",
  direction: "desc",
};

const TIER_LABELS: Record<string, string> = {
  verified: "已验证",
  provisional: "临时验证",
  exploratory: "探索验证",
};

const CERTIFICATION_LABELS: Record<string, string> = {
  certified: "安全认证",
  watchlist: "观察名单",
  blocked: "阻断",
};

const CERTIFICATION_TONES: Record<
  string,
  LeaderboardCertificationView["tone"]
> = {
  certified: "success",
  watchlist: "warning",
  blocked: "danger",
};

const normalizeScore = (value: number): number =>
  Number.isFinite(value) ? value : Number.NEGATIVE_INFINITY;

export const getLeaderboardSortOption = (
  key: LeaderboardSortKey,
): LeaderboardSortOption =>
  LEADERBOARD_SORT_OPTIONS.find((option) => option.key === key) ??
  LEADERBOARD_SORT_OPTIONS[0];

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

export const formatLeaderboardScore = (value?: number | null): string =>
  typeof value === "number" && Number.isFinite(value)
    ? value.toFixed(1)
    : "未返回";

export const getLeaderboardRankTone = (rankNo: number): LeaderboardRankTone => {
  if (rankNo === 1) return "gold";
  if (rankNo === 2) return "silver";
  if (rankNo === 3) return "bronze";
  return "base";
};

export const getLeaderboardCertificationView = (
  verificationTier: string,
  safetyCertification: string,
): LeaderboardCertificationView => {
  const tier = verificationTier.trim();
  const certification = safetyCertification.trim();

  return {
    tierLabel: TIER_LABELS[tier] ?? (tier || "未认证"),
    certificationLabel:
      CERTIFICATION_LABELS[certification] ?? (certification || "未返回"),
    tone: CERTIFICATION_TONES[certification] ?? "muted",
  };
};
