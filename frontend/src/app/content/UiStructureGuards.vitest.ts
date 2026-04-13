import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const frontendRoot = resolve(import.meta.dirname, "..", "..");

const readFrontendFile = (path: string) =>
  readFileSync(resolve(frontendRoot, path), "utf8");

describe("ui structure guards", () => {
  it("keeps evaluation detail without hero chips", () => {
    const detailContent = readFrontendFile(
      "modules/evaluation/pages/EvaluationDetailPage.vue",
    );
    const detailLogicContent = readFrontendFile(
      "modules/evaluation/composables/useEvaluationDetailPage.ts",
    );

    expect(detailContent.includes(':chips="heroChips"')).toBe(false);
    expect(
      detailContent.includes('class="progress-panel ui-surface-white"'),
    ).toBe(false);
    expect(detailLogicContent.includes("const heroChips = computed")).toBe(
      false,
    );
  });

  it("keeps dataset result count outside the filter header", () => {
    const catalogContent = readFrontendFile(
      "modules/dataset/pages/DatasetCatalogPage.vue",
    );
    const filterBarContent = readFrontendFile(
      "modules/dataset/components/DatasetFilterBar.vue",
    );

    expect(catalogContent.includes(':result-count="resultCount"')).toBe(false);
    expect(filterBarContent.includes("head-result")).toBe(false);
    expect(filterBarContent.includes("resultCount: number;")).toBe(false);
  });

  it("keeps workspace navigation with shared button usage", () => {
    const navBarContent = readFrontendFile("app/shell/NavBarShell.vue");

    expect(navBarContent.includes('item.key !== "home"')).toBe(false);
    expect(navBarContent.includes("nav-link--with-icon")).toBe(true);
    expect(navBarContent.includes("UiButton")).toBe(true);
  });
});
