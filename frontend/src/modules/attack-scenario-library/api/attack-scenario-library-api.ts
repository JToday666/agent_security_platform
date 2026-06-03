import request from "@/shared/api/http-client";
import { getCurrentDisplayLocale } from "@/app/i18n";
import { translateRuntimeMessage } from "@/app/i18n/runtime-translator";
import {
  readMemoryCache,
  setMemoryCache,
  withMemoryCache,
} from "@/shared/api/memory-cache";
import {
  adaptAttackScenarioCatalog,
  adaptEvaluationItemDetail,
} from "@/modules/attack-scenario-library/api/adapters/attack-scenario-library-adapters";
import type {
  AttackScenarioCatalogResponse,
  EvaluationItemDetail,
} from "@/shared/types/attack-scenario-library-types";

interface AttackScenarioCatalogRequestOptions {
  signal?: AbortSignal;
  force?: boolean;
}

interface EvaluationItemDetailRequestOptions {
  signal?: AbortSignal;
  force?: boolean;
}

export interface AttackScenarioLibraryServiceError extends Error {
  code?: number;
}

const createAttackScenarioLibraryServiceError = (
  message: string,
  code?: number,
): AttackScenarioLibraryServiceError => {
  const error = new Error(message) as AttackScenarioLibraryServiceError;
  error.code = code;
  return error;
};

const ATTACK_SCENARIO_CATALOG_CACHE_KEY = "attack-scenarios:catalog";
const EVALUATION_ITEM_DETAIL_CACHE_PREFIX = "attack-scenarios:evaluation-item";

const localizedCacheKey = (key: string): string =>
  `${key}:${getCurrentDisplayLocale()}`;

const evaluationItemDetailCacheKey = (evaluationItemId: string): string =>
  localizedCacheKey(
    `${EVALUATION_ITEM_DETAIL_CACHE_PREFIX}:${evaluationItemId.trim()}`,
  );

const loadCatalogFromApi = async (
  signal?: AbortSignal,
): Promise<AttackScenarioCatalogResponse> => {
  const response = await request.get<unknown>(
    "/attack-scenarios/catalog",
    { signal },
  );

  if (!response.success || !response.data) {
    throw createAttackScenarioLibraryServiceError(
      response.message ||
        translateRuntimeMessage("attackScenarioLibrary.api.catalogLoadFailed"),
      response.code,
    );
  }

  return adaptAttackScenarioCatalog(response.data);
};

const loadDetailFromApi = async (
  evaluationItemId: string,
  signal?: AbortSignal,
): Promise<EvaluationItemDetail> => {
  const response = await request.get<unknown>(
    `/attack-scenarios/evaluation-items/${evaluationItemId}`,
    { signal },
  );

  if (!response.success || !response.data) {
    throw createAttackScenarioLibraryServiceError(
      response.message ||
        translateRuntimeMessage("attackScenarioLibrary.api.detailLoadFailed"),
      response.code,
    );
  }

  return adaptEvaluationItemDetail(response.data);
};

export const getAttackScenarioCatalog = async (
  options: AttackScenarioCatalogRequestOptions = {},
): Promise<AttackScenarioCatalogResponse> => {
  const { force = false, signal } = options;
  const catalogCacheKey = localizedCacheKey(ATTACK_SCENARIO_CATALOG_CACHE_KEY);

  if (signal) {
    const cached = !force
      ? readMemoryCache<AttackScenarioCatalogResponse>(catalogCacheKey)
      : undefined;

    if (cached) {
      return cached;
    }

    const catalog = await loadCatalogFromApi(signal);
    return setMemoryCache(catalogCacheKey, catalog);
  }

  return withMemoryCache(catalogCacheKey, () => loadCatalogFromApi(signal), {
    force,
  });
};

export const getEvaluationItemDetail = async (
  evaluationItemId: string,
  options: EvaluationItemDetailRequestOptions = {},
): Promise<EvaluationItemDetail> => {
  const requestedEvaluationItemId = evaluationItemId.trim();
  const { force = false, signal } = options;
  const cacheKey = evaluationItemDetailCacheKey(requestedEvaluationItemId);

  if (signal) {
    const cached = !force
      ? readMemoryCache<EvaluationItemDetail>(cacheKey)
      : undefined;

    if (cached) {
      return cached;
    }

    const detail = await loadDetailFromApi(requestedEvaluationItemId, signal);
    return setMemoryCache(cacheKey, detail);
  }

  return withMemoryCache(
    cacheKey,
    () => loadDetailFromApi(requestedEvaluationItemId, signal),
    { force },
  );
};
