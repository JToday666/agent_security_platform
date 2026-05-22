import { describe, expect, it } from "vitest";
import {
  buildDatasetCatalogView,
  DATASET_CATALOG_ALL_CATEGORY_ID,
} from "@/modules/dataset/model/dataset-catalog-view";
import type { DatasetCategory } from "@/shared/types/dataset-types";

const catalog: DatasetCategory[] = [
  {
    categoryId: "confidentiality",
    name: "机密性",
    meaning: "敏感信息保护与最小暴露。",
    description: "面向验证码、身份信息和凭证密钥等敏感资产的泄露风险。",
    sort: 1,
    enabled: true,
    subcategoryCount: 2,
    subcategories: [
      {
        datasetId: "internal-a",
        name: "身份信息泄露",
        shortDescription: "评估代理保护姓名和验证码的能力。",
        sampleCount: 150,
        updatedAt: "2026-03-20T00:00:00Z",
        enabled: true,
      },
      {
        datasetId: "internal-b",
        name: "凭证与密钥泄露",
        shortDescription: "评估代理保护 API key 和 SSH 凭据的能力。",
        sampleCount: 267,
        updatedAt: "2026-03-21T00:00:00Z",
        enabled: true,
      },
    ],
  },
  {
    categoryId: "integrity",
    name: "完整性",
    meaning: "关键内容和文件不可篡改。",
    description: "面向文件、表单和系统配置被代理误改的风险。",
    sort: 2,
    enabled: true,
    subcategoryCount: 1,
    subcategories: [
      {
        datasetId: "internal-c",
        name: "本地文件篡改",
        shortDescription: "评估代理是否会被诱导修改本地文件。",
        sampleCount: 57,
        updatedAt: "2026-03-22T00:00:00Z",
        enabled: true,
      },
    ],
  },
];

describe("buildDatasetCatalogView", () => {
  it("summarizes the full catalog and sorts all datasets by sample count", () => {
    const view = buildDatasetCatalogView(
      catalog,
      DATASET_CATALOG_ALL_CATEGORY_ID,
      "",
      "samples-desc",
    );

    expect(view.summary).toEqual({
      categoryCount: 2,
      datasetCount: 3,
      sampleCount: 474,
      updatedAt: "2026-03-22T00:00:00Z",
    });
    expect(view.results.map((item) => item.name)).toEqual([
      "凭证与密钥泄露",
      "身份信息泄露",
      "本地文件篡改",
    ]);
  });

  it("filters by active category and includes category metadata in search", () => {
    const activeCategoryView = buildDatasetCatalogView(
      catalog,
      "integrity",
      "",
      "samples-desc",
    );

    expect(activeCategoryView.results.map((item) => item.name)).toEqual([
      "本地文件篡改",
    ]);

    const categorySearchView = buildDatasetCatalogView(
      catalog,
      DATASET_CATALOG_ALL_CATEGORY_ID,
      "最小暴露",
      "samples-desc",
    );

    expect(categorySearchView.results.map((item) => item.name)).toEqual([
      "凭证与密钥泄露",
      "身份信息泄露",
    ]);
  });
});
