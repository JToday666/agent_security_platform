import { describe, expect, it } from "vitest";
import {
  getCategoryTheme,
  getCategoryThemeMap,
} from "@/modules/dataset/lib/dataset-utils";

describe("getCategoryTheme", () => {
  const knownCategoryIds = [
    "confidentiality",
    "integrity",
    "availability_and_destructive_harm",
    "unauthorized_execution_and_system_control",
    "fraud_impersonation_and_social_engineering",
    "content_and_societal_harm",
    "harmful_search_and_reconnaissance",
  ];

  const knownSolidColors = [
    "hsl(220 62% 45%)",
    "hsl(170 54% 34%)",
    "hsl(36 72% 42%)",
    "hsl(252 58% 52%)",
    "hsl(338 58% 43%)",
    "hsl(194 64% 38%)",
    "hsl(286 48% 45%)",
  ];

  const generatedCategoryIds = [
    "agentic_tool_misuse",
    "biosecurity_abuse",
    "cloud_supply_chain",
    "data_exfiltration",
    "economic_disruption",
    "identity_abuse",
    "model_evasion",
    "physical_security",
  ];

  const extractHue = (color: string): number => {
    const match = /^hsl\((\d+) /.exec(color);
    expect(match).not.toBeNull();

    return Number(match?.[1]);
  };

  const getHueDistance = (left: number, right: number): number => {
    const delta = Math.abs(((left - right) % 360) + 360) % 360;
    return delta > 180 ? 360 - delta : delta;
  };

  const serializeThemeMap = (categoryIds: string[]) =>
    Array.from(getCategoryThemeMap(categoryIds).entries())
      .sort(([left], [right]) => left.localeCompare(right))
      .map(([categoryId, theme]) => [categoryId, theme.solid]);

  it("uses a stable high-contrast soft palette for known risk categories", () => {
    expect(knownCategoryIds.map((categoryId) => getCategoryTheme(categoryId).solid)).toEqual(
      knownSolidColors,
    );
  });

  it("keeps known risk category colors fixed when generated categories are present", () => {
    const themes = getCategoryThemeMap([
      ...knownCategoryIds,
      ...generatedCategoryIds,
    ]);

    expect(knownCategoryIds.map((categoryId) => themes.get(categoryId)?.solid)).toEqual(
      knownSolidColors,
    );
  });

  it("builds the same full risk-domain theme map regardless of input order", () => {
    const categoryIds = [...knownCategoryIds, ...generatedCategoryIds];

    expect(serializeThemeMap(categoryIds)).toEqual(
      serializeThemeMap([...categoryIds].reverse()),
    );
  });

  it("keeps generated hues distinct from reserved hues for up to fifteen risk domains", () => {
    const themes = getCategoryThemeMap([
      ...knownCategoryIds,
      ...generatedCategoryIds,
    ]);
    const hues = [...knownCategoryIds, ...generatedCategoryIds].map((categoryId) =>
      extractHue(themes.get(categoryId)?.solid ?? ""),
    );

    for (let leftIndex = 0; leftIndex < hues.length; leftIndex += 1) {
      for (let rightIndex = leftIndex + 1; rightIndex < hues.length; rightIndex += 1) {
        expect(getHueDistance(hues[leftIndex]!, hues[rightIndex]!)).toBeGreaterThanOrEqual(
          16,
        );
      }
    }
  });

  it("resolves an individual theme from the same full risk-domain context", () => {
    const categoryIds = [...knownCategoryIds, ...generatedCategoryIds];
    const categoryId = "cloud_supply_chain";

    expect(getCategoryTheme(categoryId, categoryIds)).toEqual(
      getCategoryThemeMap(categoryIds).get(categoryId),
    );
  });
});
