import { describe, expect, it } from "vitest";
import { adaptDatasetDetail } from "@/modules/dataset/api/adapters/dataset-adapters";

describe("adaptDatasetDetail", () => {
  it("normalizes sample profile aggregate fields", () => {
    const detail = adaptDatasetDetail({
      datasetId: "D1_command_execution",
      name: "命令执行",
      category: {
        categoryId: "unauthorized_execution_and_system_control",
        name: "未授权执行与系统控制",
      },
      sampleCount: 3,
      updatedAt: "2026-05-25T00:00:00Z",
      highlights: [],
      scenarios: [],
      resources: [],
      media: [],
      sampleProfile: {
        deliveryDistribution: [
          {
            code: "popup_on_webpage",
            label: "网页弹窗或覆盖层",
            count: 2,
            ratio: 0.6667,
          },
        ],
        assetTypeTop: [
          {
            code: "__unassigned__",
            label: "未标记资产",
            count: 2,
            ratio: 0.6667,
          },
        ],
        difficultyBuckets: [
          { code: "0.2-0.4", label: "0.2-0.4", count: 1, ratio: 0.3333 },
          { code: "0.4-0.6", label: "0.4-0.6", count: 1, ratio: 0.3333 },
        ],
      },
    });

    expect(Object.keys(detail.sampleProfile).sort()).toEqual([
      "assetTypeTop",
      "deliveryDistribution",
      "difficultyBuckets",
    ]);
    expect(detail.sampleProfile.assetTypeTop[0]?.code).toBe("__unassigned__");
    expect(detail.sampleProfile.difficultyBuckets.map((item) => item.code)).toEqual([
      "0.2-0.4",
      "0.4-0.6",
    ]);
  });
});
