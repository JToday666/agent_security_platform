import type {
  AttackScenarioCatalogItem,
  EvaluationItemCatalogItem,
  RiskDomainCatalogItem,
} from "@/shared/types/attack-scenario-library-types";

export type AttackScenarioCatalogSortKey =
  | "default"
  | "updated-desc"
  | "samples-desc";

export const ATTACK_SCENARIO_ALL_ID = "__all_attack_scenarios__";
export const RISK_DOMAIN_ALL_ID = "__all_risk_domains__";

export interface EvaluationItemCatalogResultItem
  extends EvaluationItemCatalogItem {
  attackScenario: AttackScenarioCatalogItem;
  riskDomain: RiskDomainCatalogItem;
}

export interface RiskDomainFilterOption {
  riskDomainId: string;
  name: string;
  count: number;
  sampleCount: number;
  attackScenario?: AttackScenarioCatalogItem;
  riskDomain?: RiskDomainCatalogItem;
}

const normalizeSearch = (value: string): string => value.trim().toLowerCase();

const normalizeTimestamp = (value?: string | null): number => {
  const parsed = Date.parse(value ?? "");

  return Number.isFinite(parsed) ? parsed : 0;
};

const matchesSearch = (
  item: EvaluationItemCatalogResultItem,
  normalizedSearch: string,
): boolean => {
  if (!normalizedSearch) {
    return true;
  }

  const haystacks = [
    item.name,
    item.shortDescription ?? "",
    item.attackScenario.name,
    item.attackScenario.description ?? "",
    item.riskDomain.name,
    item.riskDomain.meaning ?? "",
    item.riskDomain.description ?? "",
  ].map((value) => value.toLowerCase());

  return haystacks.some((value) => value.includes(normalizedSearch));
};

const compareByUpdatedAt = (
  left: EvaluationItemCatalogItem,
  right: EvaluationItemCatalogItem,
): number =>
  normalizeTimestamp(right.updatedAt) - normalizeTimestamp(left.updatedAt) ||
  left.name.localeCompare(right.name, "zh-CN");

const compareBySampleCount = (
  left: EvaluationItemCatalogItem,
  right: EvaluationItemCatalogItem,
): number =>
  (right.sampleCount ?? -1) - (left.sampleCount ?? -1) ||
  compareByUpdatedAt(left, right);

const sortEvaluationItems = (
  evaluationItems: EvaluationItemCatalogResultItem[],
  sortKey: AttackScenarioCatalogSortKey,
): EvaluationItemCatalogResultItem[] => {
  if (sortKey === "updated-desc") {
    return [...evaluationItems].sort(compareByUpdatedAt);
  }

  if (sortKey === "samples-desc") {
    return [...evaluationItems].sort(compareBySampleCount);
  }

  return [...evaluationItems];
};

const flattenEvaluationItems = (
  attackScenarios: AttackScenarioCatalogItem[],
): EvaluationItemCatalogResultItem[] =>
  attackScenarios.flatMap((attackScenario) =>
    attackScenario.riskDomains.flatMap((riskDomain) =>
      riskDomain.evaluationItems.map((evaluationItem) => ({
        ...evaluationItem,
        attackScenario,
        riskDomain,
      })),
    ),
  );

const sumSamples = (items: EvaluationItemCatalogItem[]): number =>
  items.reduce((total, item) => total + (item.sampleCount ?? 0), 0);

const resolveLatestUpdatedAt = (
  items: EvaluationItemCatalogItem[],
): string | null => {
  const latest = items.reduce<EvaluationItemCatalogItem | null>(
    (current, item) => {
      if (!current) {
        return item;
      }

      return normalizeTimestamp(item.updatedAt) >
        normalizeTimestamp(current.updatedAt)
        ? item
        : current;
    },
    null,
  );

  return latest?.updatedAt ?? null;
};

const buildFilterOptions = (
  attackScenarios: AttackScenarioCatalogItem[],
  activeAttackScenario: AttackScenarioCatalogItem | null,
): RiskDomainFilterOption[] => {
  const scopedScenarios = activeAttackScenario
    ? [activeAttackScenario]
    : attackScenarios;
  const scopedItems = flattenEvaluationItems(scopedScenarios);

  return [
    {
      riskDomainId: RISK_DOMAIN_ALL_ID,
      name: activeAttackScenario?.name ?? "all",
      count: scopedItems.length,
      sampleCount: sumSamples(scopedItems),
      attackScenario: activeAttackScenario ?? undefined,
    },
    ...scopedScenarios.flatMap((attackScenario) =>
      attackScenario.riskDomains.map((riskDomain) => ({
        riskDomainId: riskDomain.riskDomainId,
        name: riskDomain.name,
        count: riskDomain.evaluationItems.length,
        sampleCount: sumSamples(riskDomain.evaluationItems),
        attackScenario,
        riskDomain,
      })),
    ),
  ];
};

export const buildAttackScenarioCatalogView = (
  attackScenarios: AttackScenarioCatalogItem[],
  activeAttackScenarioId: string,
  activeRiskDomainId: string,
  search: string,
  sortKey: AttackScenarioCatalogSortKey,
) => {
  const normalizedSearch = normalizeSearch(search);
  const activeAttackScenario =
    activeAttackScenarioId === ATTACK_SCENARIO_ALL_ID
      ? null
      : attackScenarios.find(
          (scenario) => scenario.attackScenarioId === activeAttackScenarioId,
        ) ?? null;
  const scopedAttackScenarios = activeAttackScenario
    ? [activeAttackScenario]
    : attackScenarios;
  const activeRiskDomain =
    activeRiskDomainId === RISK_DOMAIN_ALL_ID
      ? null
      : scopedAttackScenarios
          .flatMap((scenario) => scenario.riskDomains)
          .find((riskDomain) => riskDomain.riskDomainId === activeRiskDomainId) ??
        null;
  const scopedRiskDomains = activeRiskDomain
    ? [activeRiskDomain]
    : scopedAttackScenarios.flatMap((scenario) => scenario.riskDomains);
  const scopedEvaluationItems = flattenEvaluationItems(scopedAttackScenarios).filter(
    (item) =>
      scopedRiskDomains.some(
        (riskDomain) => riskDomain.riskDomainId === item.riskDomain.riskDomainId,
      ),
  );
  const allEvaluationItems = flattenEvaluationItems(attackScenarios);
  const filteredEvaluationItems = scopedEvaluationItems.filter((item) =>
    matchesSearch(item, normalizedSearch),
  );
  const sortedEvaluationItems = sortEvaluationItems(
    filteredEvaluationItems,
    sortKey,
  );

  return {
    activeAttackScenario,
    activeAttackScenarioId:
      activeAttackScenario?.attackScenarioId ?? ATTACK_SCENARIO_ALL_ID,
    activeRiskDomain,
    activeRiskDomainId: activeRiskDomain?.riskDomainId ?? RISK_DOMAIN_ALL_ID,
    filters: buildFilterOptions(attackScenarios, activeAttackScenario),
    results: sortedEvaluationItems,
    resultCount: sortedEvaluationItems.length,
    summary: {
      attackScenarioCount: attackScenarios.length,
      riskDomainCount: attackScenarios.reduce(
        (total, scenario) => total + scenario.riskDomains.length,
        0,
      ),
      evaluationItemCount: allEvaluationItems.length,
      sampleCount: sumSamples(allEvaluationItems),
      updatedAt: resolveLatestUpdatedAt(allEvaluationItems),
    },
  };
};
