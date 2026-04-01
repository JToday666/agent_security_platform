import type { EvaluationRecord, SubmitMetaResponse } from "@/types/AgentTypes";
import type {
  DatasetCatalogResponse,
  DatasetCategory,
  DatasetDetail,
  DatasetMediaItem,
  DatasetResourceLink,
  DatasetSubcategory,
} from "@/types/DatasetTypes";

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

const createMedia = (
  datasetId: string,
  name: string,
  shortDescription: string,
  colors: [string, string],
  includeVideo = false,
): DatasetMediaItem[] => [
  {
    mediaId: `${datasetId}-image`,
    type: "image",
    title: `${name}样例概览`,
    description: "用于展示典型攻击样本与响应结构。",
    url: createSvgDataUri(name, shortDescription, colors[0], colors[1]),
  },
  ...(includeVideo
    ? [
        {
          mediaId: `${datasetId}-video`,
          type: "video" as const,
          title: `${name}运行回放`,
          description: "用于说明该类攻击在评测过程中的典型轨迹。",
          url: REFERENCE_VIDEO_URL,
          coverUrl: createSvgDataUri(
            `${name}运行回放`,
            "若外部视频不可达，页面会自动降级为不可播放提示。",
            colors[0],
            "#0f172a",
          ),
        },
      ]
    : []),
];

const createDataset = (
  datasetId: string,
  name: string,
  shortDescription: string,
  fullDescription: string,
  difficultyRange: DifficultyRange,
  sampleCount: number,
  updatedAt: string,
  highlights: string[],
  scenarios: string[],
  resources: DatasetResourceLink[],
  colors: [string, string],
  includeVideo = false,
): DatasetFixture => ({
  datasetId,
  name,
  shortDescription,
  sampleCount,
  updatedAt,
  enabled: true,
  difficultyRange,
  fullDescription,
  highlights,
  scenarios,
  resources,
  media: createMedia(datasetId, name, shortDescription, colors, includeVideo),
});

export const REFERENCE_CATALOG_VERSION = "2026-04-01T10:00:00Z";

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

const referenceCategories: CategoryFixture[] = [
  {
    categoryId: "confidentiality",
    name: "机密性",
    meaning: "防止信息泄露",
    description: "覆盖身份、密钥、隐私等高敏感信息的泄露风险。",
    sort: 1,
    enabled: true,
    subcategoryCount: 2,
    datasets: [
      createDataset(
        "A1",
        "身份信息泄露",
        "测试多轮追问和绕行提示下的身份字段泄露。",
        "该数据集围绕身份证号、手机号、地址、邮箱等高敏感字段构造多轮攻击样本，用于验证智能体是否会在追问、伪装授权和历史会话回放中回显真实信息。",
        { min: 0, max: 0.5 },
        1280,
        "2026-03-28T12:00:00Z",
        [
          "覆盖直接索取、间接诱导和历史会话挖掘。",
          "适合验证脱敏、拒答和重写策略。",
        ],
        ["客服场景下回显用户手机号。", "知识助手回显员工实名与邮箱。"],
        [
          {
            label: "查看字段说明",
            url: "https://example.com/docs/datasets/A1",
            type: "docs",
          },
        ],
        ["#2563eb", "#7c3aed"],
        true,
      ),
      createDataset(
        "A2",
        "凭证与密钥暴露",
        "聚焦 API Token、云密钥和内部凭证的泄露场景。",
        "该数据集强调配置文件、日志片段和运维命令中的凭证内容，验证模型是否会直接回显、拼接或重建敏感密钥。",
        { min: 0.4, max: 0.9 },
        960,
        "2026-03-30T09:30:00Z",
        [
          "覆盖 Token、云密钥、数据库连接串。",
          "适合联动日志与配置访问场景测试。",
        ],
        ["运维助手回显数据库连接串。", "审查机器人输出隐藏密钥。"],
        [
          {
            label: "接入建议",
            url: "https://example.com/docs/datasets/A2",
            type: "docs",
          },
        ],
        ["#0f766e", "#0ea5e9"],
      ),
    ],
  },
  {
    categoryId: "integrity",
    name: "完整性",
    meaning: "抵抗指令篡改",
    description: "评估输入污染和工具结果被篡改时的稳健性。",
    sort: 2,
    enabled: true,
    subcategoryCount: 2,
    datasets: [
      createDataset(
        "B1",
        "指令篡改",
        "测试主任务指令被覆盖、替换和诱导偏航的风险。",
        "该数据集围绕任务覆盖、角色伪造与高优先级指令伪造构造样本，重点观察智能体是否能坚持原始目标与输出约束。",
        { min: 0.2, max: 0.8 },
        1430,
        "2026-03-29T16:15:00Z",
        [
          "覆盖 JSON、Markdown 和自然语言混排注入。",
          "适合评估多代理编排链路。",
        ],
        [
          "流程代理被伪造系统消息要求跳过校验。",
          "问答助手被追加营销导向内容。",
        ],
        [
          {
            label: "数据集说明",
            url: "https://example.com/docs/datasets/B1",
            type: "docs",
          },
        ],
        ["#7c3aed", "#ec4899"],
      ),
      createDataset(
        "B2",
        "工具调用污染",
        "模拟工具返回值被污染后继续驱动错误决策。",
        "该数据集将工具结果、检索片段和函数返回值视为可污染输入，用于检验模型是否对外部工具结果过度信任。",
        { min: 0.5, max: 1 },
        840,
        "2026-03-26T14:00:00Z",
        [
          "覆盖搜索结果污染、函数返回值注入。",
          "适合验证工具 schema 与结果校验。",
        ],
        [
          "检索增强问答将恶意网页内容当成事实。",
          "插件假响应触发后续错误动作。",
        ],
        [
          {
            label: "演示脚本",
            url: "https://example.com/demo/datasets/B2",
            type: "demo",
          },
        ],
        ["#9333ea", "#2563eb"],
      ),
    ],
  },
  {
    categoryId: "availability",
    name: "可用性",
    meaning: "保障系统稳定",
    description: "聚焦资源消耗、超长上下文和高频调用下的稳定性。",
    sort: 3,
    enabled: true,
    subcategoryCount: 2,
    datasets: [
      createDataset(
        "C1",
        "资源耗尽压力",
        "评估高频并发、超长响应和大文本消耗下的降级能力。",
        "该数据集关注高频请求、长轮次生成、重复调用和大文本拼装下的稳定性表现，观察系统是否能正确限流、拒答或快速失败。",
        { min: 0.1, max: 0.6 },
        1120,
        "2026-03-27T18:10:00Z",
        ["适合观察限流、熔断和简化回答策略。", "覆盖单会话与多会话资源挤压。"],
        ["批处理机器人连续触发多轮工具链。", "高频任务同时请求长篇输出。"],
        [
          {
            label: "压测说明",
            url: "https://example.com/docs/datasets/C1",
            type: "docs",
          },
        ],
        ["#16a34a", "#0ea5e9"],
      ),
      createDataset(
        "C2",
        "长上下文拖尾",
        "测试极长上下文和复杂输入对稳定性的影响。",
        "该数据集强调上下文窗口膨胀与结构复杂度带来的稳定性问题，包含长日志、代码、表格与多层引用组合输入。",
        { min: 0.3, max: 0.7 },
        780,
        "2026-03-25T08:50:00Z",
        [
          "覆盖长日志、代码片段、表格和跨轮引用。",
          "适合发现上下文压缩策略缺陷。",
        ],
        [
          "审计助手在超长日志分析中超时。",
          "代码评审代理在多文件上下文中遗失约束。",
        ],
        [
          {
            label: "输入规范",
            url: "https://example.com/docs/datasets/C2",
            type: "docs",
          },
        ],
        ["#15803d", "#65a30d"],
      ),
    ],
  },
  {
    categoryId: "unauthorized-execution",
    name: "非授权执行",
    meaning: "阻断越权操作",
    description: "关注工具调用和系统动作的越权执行风险。",
    sort: 4,
    enabled: true,
    subcategoryCount: 2,
    datasets: [
      createDataset(
        "D1",
        "越权工具执行",
        "覆盖文件删除、网络请求和命令执行等越权调用。",
        "该数据集用于评估智能体是否会在无明确授权时调用高风险工具，覆盖文件读写、外部请求和命令执行等高风险动作。",
        { min: 0.6, max: 1 },
        1310,
        "2026-03-31T11:20:00Z",
        ["覆盖显式与隐式工具调用诱导。", "适合观察确认机制和人工兜底策略。"],
        [
          "自动化助手在缺少确认时触发文件删除。",
          "运维代理被诱导执行外部命令。",
        ],
        [
          {
            label: "风险动作清单",
            url: "https://example.com/docs/datasets/D1",
            type: "docs",
          },
        ],
        ["#ea580c", "#f97316"],
        true,
      ),
      createDataset(
        "D2",
        "越权系统操作",
        "测试环境变量、配置文件和权限提升相关的越权行为。",
        "该数据集关注系统层越权操作，包括读取本地配置、扩展权限和跨租户访问，强调拒绝动作与拒绝理由都要清晰。",
        { min: 0.8, max: 1 },
        905,
        "2026-03-24T15:45:00Z",
        [
          "覆盖环境变量、配置文件与权限提升请求。",
          "适合验证策略引擎与执行器权限矩阵。",
        ],
        [
          "代理尝试读取本地环境变量中的访问密钥。",
          "用户伪造紧急授权要求提升执行权限。",
        ],
        [
          {
            label: "接入配置建议",
            url: "https://example.com/docs/datasets/D2",
            type: "docs",
          },
        ],
        ["#c2410c", "#f59e0b"],
      ),
    ],
  },
];

const buildCatalogCategory = (
  category: CategoryFixture,
  difficulty?: number,
): DatasetCategory | null => {
  const datasets = category.datasets.filter((item) => {
    if (typeof difficulty !== "number") {
      return item.enabled;
    }

    return (
      item.enabled &&
      item.difficultyRange.min <= difficulty &&
      item.difficultyRange.max >= difficulty
    );
  });

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
      ({ difficultyRange: _, ...dataset }) => dataset,
    ),
  };
};

export const buildReferenceDatasetCatalog = (
  difficulty?: number,
): DatasetCatalogResponse => {
  const categories = referenceCategories
    .map((category) => buildCatalogCategory(category, difficulty))
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

export const getReferenceDatasetIds = (difficulty?: number): string[] =>
  buildReferenceDatasetCatalog(difficulty).categories.flatMap((category) =>
    category.subcategories.map((item) => item.datasetId),
  );

export const getReferenceDatasetNameMap = (): Map<string, string> =>
  new Map(
    referenceCategories.flatMap((category) =>
      category.datasets.map((item) => [item.datasetId, item.name] as const),
    ),
  );

const datasetNameMap = getReferenceDatasetNameMap();

export const referenceEvaluationRecords: EvaluationRecord[] = [
  {
    evaluationId: "eval_20260331_001",
    agentName: "安全卫士 v1.0",
    description: "面向企业场景的多工具安全代理。",
    createdAt: "2026-03-31T10:20:00Z",
    updatedAt: "2026-03-31T11:05:00Z",
    status: "completed",
    publicToLeaderboard: true,
    datasetIds: ["A1", "B1"],
    datasetNames: ["A1", "B1"].map((item) => datasetNameMap.get(item) ?? item),
    submitMethod: "api",
    score: 94.6,
    ownerName: "张三",
    parameters: {
      difficulty: 0.5,
      timeoutMinutes: 18,
      retryEnabled: false,
    },
  },
  {
    evaluationId: "eval_20260330_002",
    agentName: "边界巡检器",
    description: "专门用于工具权限隔离的安全执行代理。",
    createdAt: "2026-03-30T08:10:00Z",
    updatedAt: "2026-03-30T08:56:00Z",
    status: "completed",
    publicToLeaderboard: false,
    datasetIds: ["D1", "D2"],
    datasetNames: ["D1", "D2"].map((item) => datasetNameMap.get(item) ?? item),
    submitMethod: "docker",
    score: 91.2,
    ownerName: "李四",
    parameters: {
      difficulty: 0.8,
      timeoutMinutes: 20,
      retryEnabled: true,
    },
  },
  {
    evaluationId: "eval_20260329_003",
    agentName: "稳态问答引擎",
    description: "强调稳定性和上下文控制的检索增强代理。",
    createdAt: "2026-03-29T13:45:00Z",
    updatedAt: "2026-03-29T14:20:00Z",
    status: "completed",
    publicToLeaderboard: true,
    datasetIds: ["C1", "C2"],
    datasetNames: ["C1", "C2"].map((item) => datasetNameMap.get(item) ?? item),
    submitMethod: "api",
    score: 88.9,
    ownerName: "王五",
    parameters: {
      difficulty: 0.4,
      timeoutMinutes: 24,
      retryEnabled: true,
    },
  },
];
