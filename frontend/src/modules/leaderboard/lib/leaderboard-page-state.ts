import {
  translateRuntimeMessage,
  type AppTranslator,
} from "@/app/i18n/runtime-translator";

interface LeaderboardErrorLike {
  code?: unknown;
  message?: unknown;
}

export interface LeaderboardErrorState {
  title: string;
  message: string;
}

const readErrorCode = (value: unknown): number | null => {
  if (!value || typeof value !== "object" || !("code" in value)) {
    return null;
  }

  const code = Number((value as LeaderboardErrorLike).code);
  return Number.isFinite(code) ? code : null;
};

const readErrorMessage = (value: unknown): string => {
  if (value instanceof Error) {
    return value.message;
  }

  if (value && typeof value === "object" && "message" in value) {
    const message = (value as LeaderboardErrorLike).message;
    return typeof message === "string" ? message.trim() : "";
  }

  return "";
};

export const resolveLeaderboardErrorState = (
  value: unknown,
  t: AppTranslator = translateRuntimeMessage,
): LeaderboardErrorState => {
  const code = readErrorCode(value);

  if (code === 401 || code === 40100) {
    return {
      title: t("leaderboard.errors.unavailableTitle"),
      message: t("leaderboard.errors.unavailableMessage"),
    };
  }

  return {
    title: t("leaderboard.errors.loadFailedTitle"),
    message: readErrorMessage(value) || t("leaderboard.api.loadFailed"),
  };
};
