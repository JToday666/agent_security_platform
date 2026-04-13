import { describe, expect, it } from "vitest";
import type { DatasetCategoryViewModel } from "../../../shared/types/DatasetTypes";
import {
  buildDatasetCatalogView,
  type DatasetCatalogSortKey,
} from "./DatasetCatalogView";

const buildCategory = (): DatasetCategoryViewModel => ({
  categoryId: "risk_auth",
  name: "Authentication",
  meaning: "bypass",
  description: "Covers authentication bypass risks.",
  sort: 1,
  enabled: true,
  subcategoryCount: 3,
  subcategories: [
    {
      datasetId: "auth-old",
      name: "Legacy auth bypass",
      shortDescription: "Covers a legacy flow.",
      sampleCount: 18,
      updatedAt: "2025-04-01T08:00:00Z",
      enabled: true,
    },
    {
      datasetId: "auth-new",
      name: "Modern auth bypass",
      shortDescription: "Covers the current login flow.",
      sampleCount: 42,
      updatedAt: "2025-05-01T08:00:00Z",
      enabled: true,
    },
    {
      datasetId: "auth-token",
      name: "Token replay",
      shortDescription: "Covers replay and tampering.",
      sampleCount: 24,
      updatedAt: "2025-03-15T08:00:00Z",
      enabled: true,
    },
  ],
});

describe("buildDatasetCatalogView", () => {
  it("keeps default order with empty search", () => {
    const category = buildCategory();

    const result = buildDatasetCatalogView(category, "", "default");

    expect(result.resultCount).toBe(3);
    expect(result.category.subcategories.map((item) => item.datasetId)).toEqual(
      ["auth-old", "auth-new", "auth-token"],
    );
  });

  it("filters datasets by name and description", () => {
    const category = buildCategory();

    const result = buildDatasetCatalogView(category, "token", "default");

    expect(result.resultCount).toBe(1);
    expect(result.category.subcategories.map((item) => item.datasetId)).toEqual(
      ["auth-token"],
    );
  });

  it("sorts by updated time and sample count", () => {
    const category = buildCategory();

    const updatedSort = buildDatasetCatalogView(
      category,
      "",
      "updated-desc" satisfies DatasetCatalogSortKey,
    );
    const sampleSort = buildDatasetCatalogView(
      category,
      "",
      "samples-desc" satisfies DatasetCatalogSortKey,
    );

    expect(
      updatedSort.category.subcategories.map((item) => item.datasetId),
    ).toEqual(["auth-new", "auth-old", "auth-token"]);
    expect(
      sampleSort.category.subcategories.map((item) => item.datasetId),
    ).toEqual(["auth-new", "auth-token", "auth-old"]);
  });
});
