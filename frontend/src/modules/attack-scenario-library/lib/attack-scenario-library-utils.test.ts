import { describe, expect, it } from "vitest";
import {
  getAttackScenarioTheme,
  getRiskDomainTheme,
} from "@/modules/attack-scenario-library/lib/attack-scenario-library-utils";

describe("attack scenario library theme utilities", () => {
  const knownAttackScenarioIds = [
    "prompt_injection",
    "model_abuse_and_unauthorized_actions",
    "knowledge_base_poisoning",
    "tool_call_hijacking",
  ];

  const knownSolidColors = [
    "hsl(220 62% 45%)",
    "hsl(340 58% 43%)",
    "hsl(154 50% 34%)",
    "hsl(38 70% 41%)",
  ];

  const riskDomainIds = [
    "confidentiality",
    "integrity",
    "availability_and_destructive_harm",
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

  it("uses a stable palette for known attack scenarios", () => {
    expect(
      knownAttackScenarioIds.map(
        (attackScenarioId) => getAttackScenarioTheme(attackScenarioId).solid,
      ),
    ).toEqual(knownSolidColors);
  });

  it("derives risk domain colors from the owning attack scenario", () => {
    const scenarioHue = extractHue(getAttackScenarioTheme("prompt_injection").solid);
    const domainHues = riskDomainIds.map((riskDomainId) =>
      extractHue(
        getRiskDomainTheme(
          "prompt_injection",
          riskDomainId,
          riskDomainIds,
        ).solid,
      ),
    );

    for (const hue of domainHues) {
      expect(getHueDistance(hue, scenarioHue)).toBeLessThanOrEqual(18);
    }
  });

  it("keeps risk domain themes deterministic", () => {
    expect(
      getRiskDomainTheme("prompt_injection", "integrity", riskDomainIds),
    ).toEqual(
      getRiskDomainTheme("prompt_injection", "integrity", riskDomainIds),
    );
  });
});
