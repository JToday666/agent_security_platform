import { afterEach, describe, expect, it, vi } from "vitest";
import {
  getLeaderboardSortOption,
  getNextLeaderboardSortState,
} from "@/modules/leaderboard/lib/leaderboard-view";
import {
  resetRuntimeTranslator,
  setRuntimeTranslator,
} from "@/app/i18n/runtime-translator";

describe("leaderboard view helpers", () => {
  afterEach(() => {
    resetRuntimeTranslator();
  });

  it("translates only the requested sort option", () => {
    const t = vi.fn((key: string) => `translated:${key}`);

    const option = getLeaderboardSortOption("unsafeRiskScore", t);

    expect(option).toEqual({
      key: "unsafeRiskScore",
      label: "translated:leaderboard.scores.riskFull",
      shortLabel: "translated:leaderboard.scores.risk",
      defaultDirection: "asc",
    });
    expect(t).toHaveBeenCalledTimes(2);
  });

  it("uses sort metadata without translating labels when switching columns", () => {
    const t = vi.fn((key: string) => key);
    setRuntimeTranslator(t);

    expect(
      getNextLeaderboardSortState(
        { key: "officialConservativeScore", direction: "desc" },
        "unsafeRiskScore",
      ),
    ).toEqual({
      key: "unsafeRiskScore",
      direction: "asc",
    });
    expect(t).not.toHaveBeenCalled();
  });
});
