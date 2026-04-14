import { describe, expect, it, vi } from "vitest";
import { useSubmitDatasetCatalog } from "./useSubmitDatasetCatalog";
import { getDatasetCatalog } from "@/modules/dataset/api/dataset-api";

vi.mock("@/modules/dataset/api/dataset-api", () => ({
  getDatasetCatalog: vi.fn(),
}));

describe("useSubmitDatasetCatalog", () => {
  it("passes force and signal to the service", async () => {
    const controller = new AbortController();
    const catalog = {
      catalogVersion: "v1",
      categoryCount: 0,
      subcategoryCount: 0,
      categories: [],
    };
    vi.mocked(getDatasetCatalog).mockResolvedValue(catalog);

    const state = useSubmitDatasetCatalog();
    const result = await state.fetchCatalog({
      force: true,
      signal: controller.signal,
    });

    expect(result).toEqual(catalog);
    expect(getDatasetCatalog).toHaveBeenCalledWith({
      force: true,
      signal: controller.signal,
    });
    expect(state.status.value).toBe("empty");
  });
});
