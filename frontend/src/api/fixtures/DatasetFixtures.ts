import type { EvaluationRecord, SubmitMetaResponse } from "@/types/AgentTypes";
import type {
  DatasetCatalogResponse,
  DatasetCategory,
  DatasetDetail,
  DatasetMediaItem,
  DatasetResourceLink,
  DatasetSubcategory,
} from "@/types/DatasetTypes";
import type {
  ReferenceCategorySeed,
  ReferenceDatasetSeed,
} from "@/constants/DatasetTaxonomy";
import { REFERENCE_DATASET_TAXONOMY } from "@/constants/DatasetTaxonomy";
import { getCategoryTheme, resolvePublicDatasetNames } from "@/utils/common";

interface DifficultyRange {
  min: number;
  max: number;
}

interface DatasetFixture extends DatasetSubcategory {
  difficultyRange: DifficultyRange;
  fullDescription: string;
  highlights: string[];
  scenarios: string[];
  resources: DatasetResourceLink[];
  media: DatasetMediaItem[];
}

interface CategoryFixture extends Omit<DatasetCategory, "subcategories"> {
  datasets: DatasetFixture[];
}

const REFERENCE_VIDEO_URL =
  "https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4";

const DIFFICULTY_PATTERNS: readonly DifficultyRange[] = [
  { min: 0, max: 0.6 },
  { min: 0.2, max: 0.8 },
  { min: 0.4, max: 1 },
  { min: 0.1, max: 0.7 },
  { min: 0.3, max: 0.9 },
];

const createSvgDataUri = (
  title: string,
  subtitle: string,
  startColor: string,
  endColor: string,
): string => {
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="1200" height="720" viewBox="0 0 1200 720">
      <defs>
        <linearGradient id="bg" x1="0%" x2="100%" y1="0%" y2="100%">
          <stop stop-color="${startColor}" offset="0%"/>
          <stop stop-color="${endColor}" offset="100%"/>
        </linearGradient>
      </defs>
      <rect width="1200" height="720" rx="40" fill="url(#bg)"/>
      <rect x="96" y="132" width="1008" height="456" rx="32" fill="rgba(255,255,255,0.16)"/>
      <circle cx="190" cy="170" r="120" fill="rgba(255,255,255,0.08)"/>
      <circle cx="1040" cy="600" r="150" fill="rgba(255,255,255,0.08)"/>
      <text x="120" y="318" font-size="64" font-family="Segoe UI, Microsoft YaHei, sans-serif" font-weight="700" fill="#ffffff">${title}</text>
      <text x="120" y="390" font-size="28" font-family="Segoe UI, Microsoft YaHei, sans-serif" fill="rgba(255,255,255,0.92)">${subtitle}</text>
    </svg>
  `;

  return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`;
};

const buildUpdatedAt = (categorySort: number, datasetIndex: number): string => {
  const day = Math.max(1, 31 - ((categorySort - 1) * 5 + datasetIndex));
  const hour = 9 + ((categorySort + datasetIndex) % 7);

  return `2026-03-${String(day).padStart(2, "0")}T${String(hour).padStart(2, "0")}:00:00Z`;
};

const buildSampleCount = (
  categorySort: number,
  datasetIndex: number,
  datasetId: string,
): number => {
  const suffix = Number(datasetId.slice(1)) || datasetIndex + 1;

  return 760 + categorySort * 118 + datasetIndex * 57 + suffix * 9;
};

const buildDifficultyRange = (
  categorySort: number,
  datasetIndex: number,
): DifficultyRange =>
  DIFFICULTY_PATTERNS[
    (categorySort + datasetIndex) % DIFFICULTY_PATTERNS.length
  ]!;

const buildHighlights = (
  category: ReferenceCategorySeed,
  dataset: ReferenceDatasetSeed,
): string[] => [
  `覆盖 ${dataset.focus[0]} 与 ${dataset.focus[1]} 的典型触发路径。`,
  "检验多轮上下文、角色伪装与任务转写条件下的安全响应一致性。",
  `适用于 ${category.name} 风险域的基线评测、策略回归与版本对比。`,
];

const buildFullDescription = (
  category: ReferenceCategorySeed,
  dataset: ReferenceDatasetSeed,
): string =>
  `${dataset.name}评测项属于${category.name}风险域，围绕${dataset.focus[0]}、${dataset.focus[1]}等高风险情境构造测试样本。该评测项重点观察智能体在面对诱导提问、任务转写、角色伪装与工具结果拼接时，能否持续保持安全边界、给出审慎响应，并避免放大${category.meaning}相关风险。数据可用于平台化基线评测、策略回归验证以及安全能力的横向对比。`;

const buildResources = (
  dataset: ReferenceDatasetSeed,
): DatasetResourceLink[] => [
  {
    label: "查看评测说明",
    url: `https://example.com/docs/datasets/${dataset.datasetId}`,
    type: "docs",
  },
  ...(dataset.includeVideo
    ? [
        {
          label: "查看演示样例",
          url: `https://example.com/demo/datasets/${dataset.datasetId}`,
          type: "demo" as const,
        },
      ]
    : []),
];

const createMedia = (
  categoryId: string,
  datasetId: string,
  name: string,
  shortDescription: string,
  includeVideo = false,
): DatasetMediaItem[] => {
  const theme = getCategoryTheme(categoryId);

  return [
    {
      mediaId: `${datasetId}-image`,
      type: "image",
      title: `${name}样例概览`,
      description: "用于展示该评测项的输入结构、风险线索与预期响应边界。",
      url: createSvgDataUri(name, shortDescription, theme.solid, theme.text),
    },
    ...(includeVideo
      ? [
          {
            mediaId: `${datasetId}-video`,
            type: "video" as const,
            title: `${name}运行回放`,
            description:
              "用于展示该评测项在模拟执行流程中的输入触发与安全响应表现。",
            url: REFERENCE_VIDEO_URL,
            coverUrl: createSvgDataUri(
              `${name}运行回放`,
              "若外部视频不可达，页面会自动降级为不可播放提示。",
              theme.solid,
              theme.text,
            ),
          },
        ]
      : []),
  ];
};

const createDataset = (
  category: ReferenceCategorySeed,
  dataset: ReferenceDatasetSeed,
  datasetIndex: number,
): DatasetFixture => ({
  datasetId: dataset.datasetId,
  name: dataset.name,
  shortDescription: dataset.shortDescription,
  sampleCount: buildSampleCount(category.sort, datasetIndex, dataset.datasetId),
  updatedAt: buildUpdatedAt(category.sort, datasetIndex),
  enabled: true,
  difficultyRange: buildDifficultyRange(category.sort, datasetIndex),
  fullDescription: buildFullDescription(category, dataset),
  highlights: buildHighlights(category, dataset),
  scenarios: [...dataset.scenarios],
  resources: buildResources(dataset),
  media: createMedia(
    category.categoryId,
    dataset.datasetId,
    dataset.name,
    dataset.shortDescription,
    dataset.includeVideo,
  ),
});

const referenceCategories: CategoryFixture[] = REFERENCE_DATASET_TAXONOMY.map(
  (category) => ({
    categoryId: category.categoryId,
    name: category.name,
    meaning: category.meaning,
    description: category.description,
    sort: category.sort,
    enabled: true,
    subcategoryCount: category.datasets.length,
    datasets: category.datasets.map((dataset, datasetIndex) =>
      createDataset(category, dataset, datasetIndex),
    ),
  }),
);

export const REFERENCE_CATALOG_VERSION = "2026-04-02T08:00:00Z";

export const referenceSubmitMeta: SubmitMetaResponse = {
  supportedMethods: ["api", "docker"],
  difficulty: {
    min: 0,
    max: 1,
    step: 0.1,
    default: 0.5,
  },
  timeoutMinutes: {
    min: 15,
    max: 30,
    step: 1,
    default: 15,
    recommendedMax: 20,
  },
  retryEnabled: {
    default: false,
  },
  publicToLeaderboard: {
    default: true,
  },
};

const buildCatalogCategory = (
  category: CategoryFixture,
): DatasetCategory | null => {
  const datasets = category.datasets.filter((item) => item.enabled);

  if (!category.enabled || datasets.length === 0) {
    return null;
  }

  return {
    categoryId: category.categoryId,
    name: category.name,
    meaning: category.meaning,
    description: category.description,
    sort: category.sort,
    enabled: category.enabled,
    subcategoryCount: datasets.length,
    subcategories: datasets.map(
      ({
        difficultyRange: _difficultyRange,
        fullDescription: _fullDescription,
        highlights: _highlights,
        scenarios: _scenarios,
        resources: _resources,
        media: _media,
        ...dataset
      }) => dataset,
    ),
  };
};

export const buildReferenceDatasetCatalog = (): DatasetCatalogResponse => {
  const categories = referenceCategories
    .map((category) => buildCatalogCategory(category))
    .filter((category): category is DatasetCategory => category !== null);

  return {
    catalogVersion: REFERENCE_CATALOG_VERSION,
    categoryCount: categories.length,
    subcategoryCount: categories.reduce(
      (total, category) => total + category.subcategoryCount,
      0,
    ),
    categories,
  };
};

export const getReferenceDatasetDetail = (
  datasetId: string,
): DatasetDetail | null => {
  for (const category of referenceCategories) {
    const dataset = category.datasets.find(
      (item) => item.datasetId === datasetId,
    );

    if (dataset) {
      return {
        datasetId: dataset.datasetId,
        name: dataset.name,
        category: {
          categoryId: category.categoryId,
          name: category.name,
          meaning: category.meaning,
        },
        shortDescription: dataset.shortDescription,
        fullDescription: dataset.fullDescription,
        sampleCount: dataset.sampleCount,
        updatedAt: dataset.updatedAt,
        highlights: dataset.highlights,
        scenarios: dataset.scenarios,
        resources: dataset.resources,
        media: dataset.media,
      };
    }
  }

  return null;
};

export const getReferenceDatasetIds = (): string[] =>
  buildReferenceDatasetCatalog().categories.flatMap((category) =>
    category.subcategories.map((item) => item.datasetId),
  );

export const getReferenceDatasetNameMap = (): Map<string, string> =>
  new Map(
    referenceCategories.flatMap((category) =>
      category.datasets.map((item) => [item.datasetId, item.name] as const),
    ),
  );

export const referenceEvaluationRecords: EvaluationRecord[] = [
  {
    evaluationId: "eval_20260402_001",
    agentName: "Guardian Mesh v2.4",
    description: "面向企业工作流的多工具安全代理基线版本。",
    createdAt: "2026-04-02T01:15:00Z",
    updatedAt: "2026-04-02T01:48:00Z",
    status: "completed",
    progressPercent: 100,
    finalReportAvailable: true,
    finalizationReason: "completed",
    publicToLeaderboard: true,
    datasetIds: ["A1", "B3", "E1"],
    datasetNames: resolvePublicDatasetNames(["A1", "B3", "E1"]),
    submitMethod: "api",
    score: 94.2,
    ownerName: "张岚",
    parameters: {
      difficulty: 0.5,
      timeoutMinutes: 18,
      retryEnabled: false,
    },
  },
  {
    evaluationId: "eval_20260401_002",
    agentName: "Boundary Sentinel",
    description: "强调执行边界、资源保护与环境稳定性的执行代理。",
    createdAt: "2026-04-01T09:10:00Z",
    updatedAt: "2026-04-01T09:46:00Z",
    status: "completed",
    progressPercent: 100,
    finalReportAvailable: true,
    finalizationReason: "completed",
    publicToLeaderboard: false,
    datasetIds: ["C4", "D1", "G1"],
    datasetNames: resolvePublicDatasetNames(["C4", "D1", "G1"]),
    submitMethod: "docker",
    score: 92.8,
    ownerName: "周衡",
    parameters: {
      difficulty: 0.7,
      timeoutMinutes: 20,
      retryEnabled: true,
    },
  },
  {
    evaluationId: "eval_20260331_003",
    agentName: "Civic Safety Writer",
    description: "用于内容安全、公众风险与外部检索约束测试的问答代理。",
    createdAt: "2026-03-31T06:40:00Z",
    updatedAt: "2026-03-31T07:05:00Z",
    status: "completed",
    progressPercent: 100,
    finalReportAvailable: true,
    finalizationReason: "completed",
    publicToLeaderboard: true,
    datasetIds: ["F2", "F6", "G2"],
    datasetNames: resolvePublicDatasetNames(["F2", "F6", "G2"]),
    submitMethod: "api",
    score: 90.6,
    ownerName: "林澈",
    parameters: {
      difficulty: 0.4,
      timeoutMinutes: 17,
      retryEnabled: false,
    },
  },
  {
    evaluationId: "eval_20260330_004",
    agentName: "Ops Control Auditor",
    description: "偏重凭证保护、系统控制与高危操作阻断的审计代理。",
    createdAt: "2026-03-30T03:20:00Z",
    updatedAt: "2026-03-30T03:59:00Z",
    status: "completed",
    progressPercent: 100,
    finalReportAvailable: true,
    finalizationReason: "completed",
    publicToLeaderboard: true,
    datasetIds: ["A5", "D3", "C2", "E4"],
    datasetNames: resolvePublicDatasetNames(["A5", "D3", "C2", "E4"]),
    submitMethod: "docker",
    score: 93.1,
    ownerName: "许闻",
    parameters: {
      difficulty: 0.6,
      timeoutMinutes: 19,
      retryEnabled: true,
    },
  },
];
