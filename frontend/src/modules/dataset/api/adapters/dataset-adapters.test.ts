import { describe, expect, it } from "vitest";
import {
  adaptDatasetCatalog,
  adaptDatasetDetail,
} from "@/modules/dataset/api/adapters/dataset-adapters";

describe("dataset adapters", () => {
  it("normalizes unknown catalog payloads without caller casts", () => {
    expect(adaptDatasetCatalog(null)).toEqual({
      catalogVersion: "",
      categoryCount: 0,
      subcategoryCount: 0,
      categories: [],
    });
  });

  it("normalizes unknown detail payloads without caller casts", () => {
    const detail = adaptDatasetDetail({
      datasetId: "dataset-1",
      name: "Dataset",
      category: {
        categoryId: "category-1",
        name: "Category",
      },
      resources: [{ url: "/files/example.pdf" }],
      media: [{ type: "image", url: "/uploads/example.png" }],
    });

    expect(detail.datasetId).toBe("dataset-1");
    expect(detail.category.categoryId).toBe("category-1");
    expect(detail.resources).toHaveLength(1);
    expect(detail.media).toHaveLength(1);
  });
});
