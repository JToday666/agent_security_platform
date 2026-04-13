import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const frontendRoot = resolve(import.meta.dirname, "..", "..");

const readFrontendFile = (path: string) =>
  readFileSync(resolve(frontendRoot, path), "utf8");

describe("ui copy guards", () => {
  it("removes known developer-facing copy markers", () => {
    const auditedEntries: Array<{ path: string; phrases: string[] }> = [
      {
        path: "modules/public/pages/HomePage.vue",
        phrases: ["Product Story", "Competition Ready"],
      },
      {
        path: "modules/public/pages/LeaderboardPage.vue",
        phrases: ["Coming Soon", "Leaderboard Mock", "mockRows", "showMock"],
      },
      {
        path: "modules/submission/pages/SubmitAgentPage.vue",
        phrases: ["Submission Summary", "submit-note"],
      },
      {
        path: "modules/evaluation/pages/EvaluationDetailPage.vue",
        phrases: ["layout rationale", "review note"],
      },
    ];

    for (const entry of auditedEntries) {
      const content = readFrontendFile(entry.path);

      for (const phrase of entry.phrases) {
        expect(
          content.includes(phrase),
          `${entry.path} should not include "${phrase}"`,
        ).toBe(false);
      }
    }
  });

  it("keeps the upgraded home layout markers", () => {
    const homeContent = readFrontendFile("modules/public/pages/HomePage.vue");

    expect(homeContent.includes("HomeStatsRow")).toBe(true);
    expect(homeContent.includes("HomeWorkflowCard")).toBe(true);
    expect(homeContent.includes("hero-grid")).toBe(true);
    expect(homeContent.includes("workflow-grid")).toBe(true);
    expect(homeContent.includes('class="hero-title ui-title-gradient"')).toBe(
      true,
    );
    expect(homeContent.includes("hero-description--desktop-single-line")).toBe(
      true,
    );
  });
});
