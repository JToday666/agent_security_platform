import { describe, expect, it } from "vitest";
import { buildDynamicValueAxisRange } from "@/modules/evaluation/lib/evaluation-report-chart-options";

describe("buildDynamicValueAxisRange", () => {
  it("returns the full range when full axis mode is selected", () => {
    expect(
      buildDynamicValueAxisRange([3.7, 4.9, 5.2], {
        mode: "full",
        fullMin: 0,
        fullMax: 100,
      }),
    ).toEqual({
      min: 0,
      max: 100,
      interval: 20,
    });
  });

  it("focuses a clustered score range with readable ticks", () => {
    expect(
      buildDynamicValueAxisRange([3.7, 4.9, 5.2], {
        mode: "focus",
        fullMin: 0,
        fullMax: 100,
      }),
    ).toEqual({
      min: 3.5,
      max: 5.5,
      interval: 0.5,
    });
  });

  it("focuses clustered duration values without forcing zero", () => {
    expect(
      buildDynamicValueAxisRange([1835, 1901], {
        mode: "focus",
        targetTickCount: 4,
      }),
    ).toEqual({
      min: 1820,
      max: 1920,
      interval: 20,
    });
  });

  it("falls back to a small useful range for a single point", () => {
    expect(
      buildDynamicValueAxisRange([4.9], {
        mode: "focus",
        fullMin: 0,
        fullMax: 100,
      }),
    ).toEqual({
      min: 4,
      max: 6,
      interval: 0.5,
    });
  });

  it("uses the full range for empty data", () => {
    expect(
      buildDynamicValueAxisRange([], {
        mode: "focus",
        fullMin: 0,
        fullMax: 1,
      }),
    ).toEqual({
      min: 0,
      max: 1,
      interval: 0.2,
    });
  });
});
