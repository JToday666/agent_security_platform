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
): LeaderboardErrorState => {
  const code = readErrorCode(value);

  if (code === 401 || code === 40100) {
    return {
      title: "排行榜暂不可用",
      message: "公开排行榜暂时无法读取，请稍后重试。",
    };
  }

  return {
    title: "排行榜加载失败",
    message: readErrorMessage(value) || "排行榜加载失败，请稍后重试。",
  };
};
