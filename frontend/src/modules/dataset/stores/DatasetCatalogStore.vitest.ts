import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  getDatasetCatalog,
  getDatasetDetail,
} from "@/modules/dataset/api/DatasetService";
import { useDatasetCatalogStore } from "./DatasetCatalogStore";

vi.mock("@/modules/dataset/api/DatasetService", () => ({
  getDatasetCatalog: vi.fn(),
  getDatasetDetail: vi.fn(),
}));

describe("DatasetCatalogStore", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it("passes force when fetching the catalog", async () => {
    vi.mocked(getDatasetCatalog).mockResolvedValue({
      catalogVersion: "v1",
      categoryCount: 0,
      subcategoryCount: 0,
      categories: [],
    });

    const store = useDatasetCatalogStore();
    await store.fetchCatalog(true);

    expect(getDatasetCatalog).toHaveBeenCalledWith({ force: true });
  });

  it("passes force when fetching a dataset detail", async () => {
    vi.mocked(getDatasetDetail).mockResolvedValue({
      datasetId: "dataset-1",
      name: "Dataset 1",
      shortDescription: "desc",
      fullDescription: "full",
      sampleCount: 1,
      updatedAt: "2026-01-01T00:00:00Z",
      category: {
        categoryId: "risk",
        name: "Risk",
        meaning: "risk",
      },
      highlights: [],
      scenarios: [],
      resources: [],
      media: [],
    });

    const store = useDatasetCatalogStore();
    await store.fetchDatasetDetailById("dataset-1", true);

    expect(getDatasetDetail).toHaveBeenCalledWith("dataset-1", { force: true });
  });
});
