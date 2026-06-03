import { translateRuntimeMessage } from "@/app/i18n/runtime-translator";
import { computed, ref } from "vue";
import { getAttackScenarioCatalog } from "@/modules/attack-scenario-library/api/attack-scenario-library-api";
import { getErrorMessage } from "@/shared/composables/useAsyncState";
import type { AttackScenarioCatalogResponse } from "@/shared/types/attack-scenario-library-types";

export type SubmitAttackScenarioCatalogStatus =
  | "idle"
  | "loading"
  | "refreshing"
  | "ready"
  | "empty"
  | "error";

interface FetchCatalogOptions {
  signal?: AbortSignal;
  force?: boolean;
}

export const useSubmitAttackScenarioCatalog = () => {
  const catalog = ref<AttackScenarioCatalogResponse | null>(null);
  const status = ref<SubmitAttackScenarioCatalogStatus>("idle");
  const errorMessage = ref("");

  const enabledAttackScenarios = computed(() =>
    (catalog.value?.attackScenarios ?? [])
      .filter((scenario) => scenario.enabled)
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

  const evaluationItemIds = computed(() =>
    enabledAttackScenarios.value.flatMap((scenario) =>
      scenario.riskDomains.flatMap((riskDomain) =>
        riskDomain.evaluationItems.map((item) => item.evaluationItemId),
      ),
    ),
  );

  const applyCatalog = (nextCatalog: AttackScenarioCatalogResponse) => {
    catalog.value = nextCatalog;
    errorMessage.value = "";
    status.value = nextCatalog.evaluationItemCount > 0 ? "ready" : "empty";
  };

  const fetchCatalog = async (
    options: FetchCatalogOptions = {},
  ): Promise<AttackScenarioCatalogResponse> => {
    if (!options.force && catalog.value) {
      applyCatalog(catalog.value);
      return catalog.value;
    }

    const hasResolvedCatalog = Boolean(catalog.value);
    status.value = hasResolvedCatalog ? "refreshing" : "loading";
    errorMessage.value = "";

    try {
      const nextCatalog = await getAttackScenarioCatalog({
        signal: options.signal,
        force: options.force,
      });

      applyCatalog(nextCatalog);
      return nextCatalog;
    } catch (error) {
      status.value = "error";
      errorMessage.value =
        getErrorMessage(
          error,
          translateRuntimeMessage("submission.errors.catalogLoadFailed"),
        );
      throw error;
    }
  };

  return {
    catalog,
    status,
    errorMessage,
    enabledAttackScenarios,
    evaluationItemIds,
    fetchCatalog,
  };
};
