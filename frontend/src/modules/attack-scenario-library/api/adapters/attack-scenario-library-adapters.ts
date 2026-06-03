import type {
  AttackScenarioCatalogResponse,
  EvaluationItemDetail,
  EvaluationItemDistributionItem,
  EvaluationItemMediaItem,
  EvaluationItemResourceLink,
  EvaluationItemSampleProfile,
  RiskDomainCatalogItem,
} from "@/shared/types/attack-scenario-library-types";
import { normalizeApiAssetUrl } from "@/shared/api/api-runtime";
import { translateRuntimeMessage } from "@/app/i18n/runtime-translator";

type UnknownRecord = Record<string, unknown>;

const toRecord = (value: unknown): UnknownRecord =>
  value && typeof value === "object" ? (value as UnknownRecord) : {};

const toStringValue = (value: unknown): string =>
  typeof value === "string" ? value.trim() : "";

const toOptionalString = (value: unknown): string | null => {
  const normalized = toStringValue(value);
  return normalized ? normalized : null;
};

const toNumberValue = (value: unknown, fallback = 0): number => {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
};

const toBooleanValue = (value: unknown, fallback = false): boolean =>
  typeof value === "boolean" ? value : fallback;

const toStringArray = (value: unknown): string[] =>
  Array.isArray(value)
    ? value.map((item) => toStringValue(item)).filter((item) => item.length > 0)
    : [];

const normalizeDistributionItem = (
  item: unknown,
): EvaluationItemDistributionItem | null => {
  if (!item || typeof item !== "object") {
    return null;
  }

  const candidate = item as UnknownRecord;
  const code = toStringValue(candidate.code);
  if (!code) {
    return null;
  }

  return {
    code,
    label: toStringValue(candidate.label) || code,
    count: Math.max(0, Math.round(toNumberValue(candidate.count, 0))),
    ratio: Math.max(0, toNumberValue(candidate.ratio, 0)),
  };
};

const normalizeDistribution = (value: unknown): EvaluationItemDistributionItem[] =>
  Array.isArray(value)
    ? value
        .map((item) => normalizeDistributionItem(item))
        .filter((item): item is EvaluationItemDistributionItem => item !== null)
    : [];

const normalizeSampleProfile = (
  value: unknown,
): EvaluationItemSampleProfile => {
  const candidate = toRecord(value);

  return {
    deliveryDistribution: normalizeDistribution(candidate.deliveryDistribution),
    assetTypeTop: normalizeDistribution(candidate.assetTypeTop).slice(0, 5),
    difficultyBuckets: normalizeDistribution(candidate.difficultyBuckets),
  };
};

const normalizeResource = (
  resource: unknown,
  index: number,
): EvaluationItemResourceLink | null => {
  if (!resource || typeof resource !== "object") {
    return null;
  }

  const candidate = resource as UnknownRecord;
  const label =
    toStringValue(candidate.label) ||
    toStringValue(candidate.title) ||
    translateRuntimeMessage("attackScenarioLibrary.fallback.relatedResource", {
      index: index + 1,
    });
  const url = normalizeApiAssetUrl(toOptionalString(candidate.url));
  if (!url) {
    return null;
  }

  const type = toStringValue(candidate.type);
  return {
    label,
    url,
    type:
      type === "docs" || type === "download" || type === "demo" ? type : "link",
  };
};

const normalizeMedia = (
  media: unknown,
  index: number,
): EvaluationItemMediaItem | null => {
  if (!media || typeof media !== "object") {
    return null;
  }

  const candidate = media as UnknownRecord;
  const url = normalizeApiAssetUrl(toOptionalString(candidate.url));
  const type = toStringValue(candidate.type);
  if (!url || (type !== "image" && type !== "video")) {
    return null;
  }

  return {
    mediaId:
      toStringValue(candidate.mediaId) ||
      toStringValue(candidate.id) ||
      `media-${index + 1}`,
    type,
    title:
      toStringValue(candidate.title) ||
      translateRuntimeMessage("attackScenarioLibrary.fallback.media", {
        index: index + 1,
      }),
    description: toOptionalString(candidate.description),
    url,
    coverUrl: normalizeApiAssetUrl(
      toOptionalString(candidate.coverUrl) ??
        toOptionalString(candidate.poster),
    ),
    sort: candidate.sort == null ? null : toNumberValue(candidate.sort, index),
  };
};

const sortAttackScenarios = (
  left: AttackScenarioCatalogResponse["attackScenarios"][number],
  right: AttackScenarioCatalogResponse["attackScenarios"][number],
): number =>
  toNumberValue(left.sort, Number.MAX_SAFE_INTEGER) -
    toNumberValue(right.sort, Number.MAX_SAFE_INTEGER) ||
  left.attackScenarioId.localeCompare(right.attackScenarioId);

const sortRiskDomains = (
  left: RiskDomainCatalogItem,
  right: RiskDomainCatalogItem,
): number =>
  toNumberValue(left.sort, Number.MAX_SAFE_INTEGER) -
    toNumberValue(right.sort, Number.MAX_SAFE_INTEGER) ||
  left.riskDomainId.localeCompare(right.riskDomainId);

export const adaptAttackScenarioCatalog = (
  payload: unknown,
): AttackScenarioCatalogResponse => {
  const candidate = toRecord(payload);
  const attackScenarios = Array.isArray(candidate.attackScenarios)
    ? candidate.attackScenarios
    : [];

  const normalizedAttackScenarios = attackScenarios
    .map((value) => {
      const attackScenario = toRecord(value);
      const riskDomains = Array.isArray(attackScenario.riskDomains)
        ? attackScenario.riskDomains
        : [];

      return {
        attackScenarioId: toStringValue(attackScenario.attackScenarioId),
        name:
          toStringValue(attackScenario.name) ||
          translateRuntimeMessage(
            "attackScenarioLibrary.fallback.unnamedAttackScenario",
          ),
        description: toOptionalString(attackScenario.description),
        sort:
          attackScenario.sort == null
            ? null
            : toNumberValue(attackScenario.sort),
        enabled: toBooleanValue(attackScenario.enabled, true),
        riskDomainCount: riskDomains.length,
        evaluationItemCount: Math.max(
          0,
          Math.round(toNumberValue(attackScenario.evaluationItemCount, 0)),
        ),
        sampleCount: Math.max(
          0,
          Math.round(toNumberValue(attackScenario.sampleCount, 0)),
        ),
        riskDomains: riskDomains
          .map((value) => {
            const riskDomain = toRecord(value);
            const evaluationItems = Array.isArray(riskDomain.evaluationItems)
              ? riskDomain.evaluationItems
              : [];

            return {
              riskDomainId: toStringValue(riskDomain.riskDomainId),
              name:
                toStringValue(riskDomain.name) ||
                translateRuntimeMessage(
                  "attackScenarioLibrary.fallback.unnamedRiskDomain",
                ),
              meaning: toOptionalString(riskDomain.meaning),
              description: toOptionalString(riskDomain.description),
              sort:
                riskDomain.sort == null ? null : toNumberValue(riskDomain.sort),
              enabled: toBooleanValue(riskDomain.enabled, true),
              evaluationItemCount: evaluationItems.length,
              sampleCount: Math.max(
                0,
                Math.round(toNumberValue(riskDomain.sampleCount, 0)),
              ),
              evaluationItems: evaluationItems.map((itemValue) => {
                const evaluationItem = toRecord(itemValue);

                return {
                  evaluationItemId: toStringValue(
                    evaluationItem.evaluationItemId,
                  ),
                  name:
                    toStringValue(evaluationItem.name) ||
                    translateRuntimeMessage(
                      "attackScenarioLibrary.fallback.unnamedEvaluationItem",
                    ),
                  shortDescription: toOptionalString(
                    evaluationItem.shortDescription,
                  ),
                  sampleCount:
                    evaluationItem.sampleCount == null
                      ? null
                      : toNumberValue(evaluationItem.sampleCount),
                  updatedAt: toOptionalString(evaluationItem.updatedAt),
                  enabled: toBooleanValue(evaluationItem.enabled, true),
                };
              }),
            };
          })
          .filter((riskDomain) => riskDomain.riskDomainId.length > 0)
          .sort(sortRiskDomains),
      };
    })
    .filter((attackScenario) => attackScenario.attackScenarioId.length > 0)
    .sort(sortAttackScenarios);

  return {
    catalogVersion: toStringValue(candidate.catalogVersion) || "",
    attackScenarioCount: normalizedAttackScenarios.length,
    riskDomainCount: normalizedAttackScenarios.reduce(
      (total, attackScenario) => total + attackScenario.riskDomains.length,
      0,
    ),
    evaluationItemCount: normalizedAttackScenarios.reduce(
      (total, attackScenario) =>
        total +
        attackScenario.riskDomains.reduce(
          (domainTotal, riskDomain) =>
            domainTotal + riskDomain.evaluationItems.length,
          0,
        ),
      0,
    ),
    attackScenarios: normalizedAttackScenarios,
  };
};

export const adaptEvaluationItemDetail = (
  payload: unknown,
): EvaluationItemDetail => {
  const candidate = toRecord(payload);
  const attackScenario = toRecord(candidate.attackScenario);
  const riskDomain = toRecord(candidate.riskDomain);
  const sampleCount =
    candidate.sampleCount == null ? null : toNumberValue(candidate.sampleCount);

  return {
    evaluationItemId: toStringValue(candidate.evaluationItemId),
    name:
      toStringValue(candidate.name) ||
      translateRuntimeMessage(
        "attackScenarioLibrary.fallback.unnamedEvaluationItem",
      ),
    attackScenario: {
      attackScenarioId: toStringValue(attackScenario.attackScenarioId),
      name:
        toStringValue(attackScenario.name) ||
        translateRuntimeMessage(
          "attackScenarioLibrary.fallback.unnamedAttackScenario",
        ),
      description: toOptionalString(attackScenario.description),
    },
    riskDomain: {
      riskDomainId: toStringValue(riskDomain.riskDomainId),
      name:
        toStringValue(riskDomain.name) ||
        translateRuntimeMessage(
          "attackScenarioLibrary.fallback.unnamedRiskDomain",
        ),
      meaning: toOptionalString(riskDomain.meaning),
    },
    shortDescription: toOptionalString(candidate.shortDescription),
    fullDescription: toOptionalString(candidate.fullDescription),
    sampleCount,
    updatedAt: toOptionalString(candidate.updatedAt),
    highlights: toStringArray(candidate.highlights),
    scenarios: toStringArray(candidate.scenarios),
    resources: (Array.isArray(candidate.resources) ? candidate.resources : [])
      .map((resource, index) => normalizeResource(resource, index))
      .filter(
        (resource): resource is EvaluationItemResourceLink => resource !== null,
      ),
    media: (Array.isArray(candidate.media) ? candidate.media : [])
      .map((media, index) => normalizeMedia(media, index))
      .filter((media): media is EvaluationItemMediaItem => media !== null),
    sampleProfile: normalizeSampleProfile(candidate.sampleProfile),
  };
};
