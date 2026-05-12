import { translateRuntimeMessage } from "@/app/i18n/runtime-translator";
import { ApiConfig } from "@/shared/api/Config";
import request from "@/shared/api/http-client";
import type {
  LeaderboardEntry,
  LeaderboardSnapshot,
} from "@/modules/leaderboard/types/leaderboard-types";

type UnknownRecord = Record<string, unknown>;

export interface LeaderboardServiceError extends Error {
  code?: number;
}

const toRecord = (value: unknown): UnknownRecord =>
  value && typeof value === "object" ? (value as UnknownRecord) : {};

const readField = (
  value: UnknownRecord,
  camelKey: string,
  snakeKey: string,
): unknown => value[camelKey] ?? value[snakeKey];

const toStringValue = (value: unknown): string =>
  typeof value === "string" ? value.trim() : "";

const toNumberValue = (value: unknown, fallback = 0): number => {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
};

const toScore = (value: unknown): number =>
  Number(toNumberValue(value, 0).toFixed(1));

const toPositiveInteger = (value: unknown): number =>
  Math.max(0, Math.round(toNumberValue(value, 0)));

const createLeaderboardServiceError = (
  message: string,
  code?: number,
): LeaderboardServiceError => {
  const error = new Error(message) as LeaderboardServiceError;
  error.code = code;
  return error;
};

const adaptLeaderboardEntry = (value: unknown): LeaderboardEntry => {
  const candidate = toRecord(value);

  return {
    rankNo: toPositiveInteger(readField(candidate, "rankNo", "rank_no")),
    displayName:
      toStringValue(readField(candidate, "displayName", "display_name")) ||
      translateRuntimeMessage("leaderboard.api.unnamedAgent"),
    anonymous: Boolean(readField(candidate, "anonymous", "anonymous")),
    officialConservativeScore: toScore(
      readField(
        candidate,
        "officialConservativeScore",
        "official_conservative_score",
      ),
    ),
    safeCapabilityScore: toScore(
      readField(candidate, "safeCapabilityScore", "safe_capability_score"),
    ),
    highDifficultyScore: toScore(
      readField(candidate, "highDifficultyScore", "high_difficulty_score"),
    ),
    unsafeRiskScore: toScore(
      readField(candidate, "unsafeRiskScore", "unsafe_risk_score"),
    ),
    confidence: toScore(readField(candidate, "confidence", "confidence")),
    totalSamples: toPositiveInteger(
      readField(candidate, "totalSamples", "total_samples"),
    ),
  };
};

export const adaptLeaderboardSnapshot = (
  value: unknown,
): LeaderboardSnapshot => {
  const candidate = toRecord(value);
  const entries = Array.isArray(candidate.entries)
    ? candidate.entries.map(adaptLeaderboardEntry)
    : [];

  return {
    entryCount:
      toPositiveInteger(readField(candidate, "entryCount", "entry_count")) ||
      entries.length,
    entries,
  };
};

const getLiveLeaderboardSnapshot = async (): Promise<LeaderboardSnapshot> => {
  const response = await request.get<unknown>("/leaderboards/current", {
    skipUnauthorizedEvent: true,
  });

  if (!response.success || !response.data) {
    throw createLeaderboardServiceError(
      response.message || translateRuntimeMessage("leaderboard.api.loadFailed"),
      response.code,
    );
  }

  return adaptLeaderboardSnapshot(response.data);
};

const getMockLeaderboardSnapshot = async (): Promise<LeaderboardSnapshot> => {
  const { mockLeaderboardSnapshot } =
    await import("@/modules/leaderboard/mock/leaderboard-fixtures");
  return adaptLeaderboardSnapshot(mockLeaderboardSnapshot);
};

export const getLeaderboardSnapshot = async (): Promise<LeaderboardSnapshot> =>
  ApiConfig.enableApiMock
    ? getMockLeaderboardSnapshot()
    : getLiveLeaderboardSnapshot();
