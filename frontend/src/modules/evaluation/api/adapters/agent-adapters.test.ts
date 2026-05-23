import { describe, expect, it } from "vitest";
import { adaptSubmitMeta } from "./agent-adapters";
import { normalizeMaxSteps } from "@/modules/submission/model/parameter-validator";

describe("adaptSubmitMeta", () => {
  it("defaults maxSteps step to 1 when the backend omits it", () => {
    const meta = adaptSubmitMeta({
      supportedMethods: ["api"],
      difficulty: { min: 0, max: 1, step: 0.1, default: 0.5 },
      timeoutMinutes: { min: 15, max: 30, step: 1, default: 15 },
      maxSteps: { min: 1, max: 100, default: 30 },
      leaderboardDisplayMode: {
        default: "public",
        options: ["public", "anonymous"],
      },
    });

    expect(meta.maxSteps.step).toBe(1);
    expect(normalizeMaxSteps(42, meta.maxSteps)).toBe(42);
  });

  it("treats a zero step as a unit step fallback", () => {
    const meta = adaptSubmitMeta({
      supportedMethods: ["api"],
      difficulty: { min: 0, max: 1, step: 0.1, default: 0.5 },
      timeoutMinutes: { min: 15, max: 30, step: 1, default: 15 },
      maxSteps: { min: 1, max: 100, step: 0, default: 30 },
      leaderboardDisplayMode: {
        default: "public",
        options: ["public", "anonymous"],
      },
    });

    expect(meta.maxSteps.step).toBe(1);
    expect(Number.isFinite(normalizeMaxSteps(42, meta.maxSteps))).toBe(true);
  });
});
