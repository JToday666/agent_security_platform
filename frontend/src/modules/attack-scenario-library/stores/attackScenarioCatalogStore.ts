import { computed, ref } from "vue";
import { defineStore } from "pinia";
import { getCurrentDisplayLocale } from "@/app/i18n";
import { translateRuntimeMessage } from "@/app/i18n/runtime-translator";
import {
  getAttackScenarioCatalog,
  getEvaluationItemDetail,
  type AttackScenarioLibraryServiceError,
} from "@/modules/attack-scenario-library/api/attack-scenario-library-api";
import { getErrorMessage } from "@/shared/composables/useAsyncState";
import type {
  AttackScenarioCatalogItem,
  EvaluationItemCatalogItem,
  EvaluationItemDetail,
} from "@/shared/types/attack-scenario-library-types";

interface EvaluationItemDetailFetchResult {
  detail: EvaluationItemDetail | null;
  notFound: boolean;
  errorMessage: string;
}

const isEnabledAttackScenario = (scenario: AttackScenarioCatalogItem): boolean =>
  scenario.enabled;

export const useAttackScenarioCatalogStore = defineStore(
  "attackScenarioCatalog",
  () => {
    const catalogVersion = ref("");
    const attackScenarios = ref<AttackScenarioCatalogItem[]>([]);
    const loading = ref(false);
    const loaded = ref(false);
    const loadedLocale = ref("");
    const error = ref("");
    const detailCache = ref<Record<string, EvaluationItemDetail>>({});

    const enabledAttackScenarios = computed(() =>
      attackScenarios.value
        .filter(isEnabledAttackScenario)
        .map((scenario) => ({
          ...scenario,
          riskDomains: scenario.riskDomains
            .filter((riskDomain) => riskDomain.enabled)
            .map((riskDomain) => ({
              ...riskDomain,
              evaluationItems: riskDomain.evaluationItems.filter(
                (item) => item.enabled,
              ),
            })),
        })),
    );

    const evaluationItems = computed(() =>
      enabledAttackScenarios.value.flatMap((attackScenario) =>
        attackScenario.riskDomains.flatMap((riskDomain) =>
          riskDomain.evaluationItems.map((item) => ({
            ...item,
            attackScenario,
            riskDomain,
          })),
        ),
      ),
    );

    const fetchCatalog = async (force = false): Promise<boolean> => {
      const locale = getCurrentDisplayLocale();
      if (loaded.value && loadedLocale.value === locale && !force) return true;

      loading.value = true;
      error.value = "";

      try {
        const catalog = await getAttackScenarioCatalog({ force });
        catalogVersion.value = catalog.catalogVersion;
        attackScenarios.value = catalog.attackScenarios;
        loaded.value = true;
        loadedLocale.value = locale;
        return true;
      } catch (fetchError) {
        error.value =
          getErrorMessage(
            fetchError,
            translateRuntimeMessage(
              "attackScenarioLibrary.api.catalogLoadFailed",
            ),
          );
        return false;
      } finally {
        loading.value = false;
      }
    };

    const fetchEvaluationItemDetailById = async (
      evaluationItemId: string,
      force = false,
    ): Promise<EvaluationItemDetailFetchResult> => {
      const cacheKey = `${getCurrentDisplayLocale()}:${evaluationItemId}`;

      if (detailCache.value[cacheKey] && !force) {
        return {
          detail: detailCache.value[cacheKey],
          notFound: false,
          errorMessage: "",
        };
      }

      try {
        const detail = await getEvaluationItemDetail(evaluationItemId, { force });
        detailCache.value = {
          ...detailCache.value,
          [cacheKey]: detail,
        };
        return {
          detail,
          notFound: false,
          errorMessage: "",
        };
      } catch (fetchError) {
        const fetchResultError =
          fetchError as AttackScenarioLibraryServiceError;
        return {
          detail: null,
          notFound: fetchResultError.code === 40400,
          errorMessage:
            fetchResultError.message ||
            (fetchResultError.code === 40400
              ? translateRuntimeMessage("attackScenarioLibrary.api.notFound")
              : translateRuntimeMessage(
                  "attackScenarioLibrary.api.detailLoadFailed",
                )),
        };
      }
    };

    const getEvaluationItemSummaryById = (
      evaluationItemId: string,
    ): EvaluationItemCatalogItem | null =>
      evaluationItems.value.find(
        (item) => item.evaluationItemId === evaluationItemId,
      ) ?? null;

    return {
      catalogVersion,
      attackScenarios,
      loading,
      loaded,
      error,
      enabledAttackScenarios,
      evaluationItems,
      fetchCatalog,
      fetchEvaluationItemDetailById,
      getEvaluationItemSummaryById,
    };
  },
);
