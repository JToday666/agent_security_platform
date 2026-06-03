<template>
  <div class="content attack-scenario-library-page layout-page-shell">
    <PageHero
      :title="t('attackScenarioLibrary.pages.catalog.title')"
      :description="t('attackScenarioLibrary.pages.catalog.description')"
    />

    <PageStatePanel
      v-if="loading && !loaded"
      :title="t('attackScenarioLibrary.pages.catalog.loadingTitle')"
      :message="t('attackScenarioLibrary.pages.catalog.loadingMessage')"
      :loading="true"
    />

    <PageStatePanel
      v-else-if="error && !enabledAttackScenarios.length"
      :title="t('attackScenarioLibrary.pages.catalog.loadFailedTitle')"
      :message="error"
      :action-text="t('attackScenarioLibrary.pages.catalog.reloadAction')"
      @action="reloadCatalog"
    />

    <PageStatePanel
      v-else-if="!enabledAttackScenarios.length"
      :title="t('attackScenarioLibrary.pages.catalog.emptyTitle')"
      :message="t('attackScenarioLibrary.pages.catalog.emptyMessage')"
    />

    <template v-else>
      <section class="catalog-console" aria-labelledby="dataset-catalog-heading">
        <div class="catalog-console__summary">
          <article class="summary-card">
            <span>{{ t("attackScenarioLibrary.catalog.stats.attackScenarios") }}</span>
            <strong>{{ catalogView.summary.attackScenarioCount }}</strong>
          </article>
          <article class="summary-card">
            <span>{{ t("attackScenarioLibrary.catalog.stats.riskDomains") }}</span>
            <strong>{{ catalogView.summary.riskDomainCount }}</strong>
          </article>
          <article class="summary-card">
            <span>{{ t("attackScenarioLibrary.catalog.stats.samples") }}</span>
            <strong>{{ formatSampleCount(catalogView.summary.sampleCount) }}</strong>
          </article>
          <article class="summary-card">
            <span>{{ t("attackScenarioLibrary.catalog.stats.updatedAt") }}</span>
            <strong>{{ formatDateLabel(catalogView.summary.updatedAt ?? undefined) }}</strong>
          </article>
        </div>

        <div class="catalog-console__controls" role="search">
          <FormField
            class="catalog-search"
            :label="t('attackScenarioLibrary.filter.searchLabel')"
            :model-value="search"
            type="search"
            :placeholder="t('attackScenarioLibrary.filter.searchPlaceholder')"
            leading-icon="app:action.search"
            appearance="soft"
            @update:model-value="search = $event"
          />

          <FormField
            class="catalog-sort"
            :label="t('attackScenarioLibrary.filter.sortLabel')"
            :model-value="sortKey"
            type="select"
            :options="sortOptions"
            leading-icon="app:action.sort"
            appearance="soft"
            @update:model-value="handleSortKeyChange"
          />
        </div>

        <div
          class="category-chip-strip"
          :aria-label="t('attackScenarioLibrary.catalog.attackScenarioFilter')"
        >
          <button
            v-for="scenario in scenarioTabs"
            :key="scenario.attackScenarioId"
            type="button"
            class="category-chip"
            :class="{
              active:
                catalogView.activeAttackScenarioId === scenario.attackScenarioId,
            }"
            :style="getScenarioTabStyle(scenario.attackScenarioId)"
            @click="handleAttackScenarioChange(scenario.attackScenarioId)"
          >
            <span>{{ scenario.name }}</span>
          </button>
        </div>

        <div class="catalog-console__body">
          <aside
            class="category-rail"
            :aria-label="t('attackScenarioLibrary.catalog.riskDomainFilter')"
          >
            <button
              v-for="filter in catalogView.filters"
              :key="filter.riskDomainId"
              type="button"
              class="rail-item"
              :class="{ active: catalogView.activeRiskDomainId === filter.riskDomainId }"
              :style="getFilterStyle(filter)"
              @click="activeRiskDomainId = filter.riskDomainId"
            >
              <span class="rail-item__dot" aria-hidden="true"></span>
              <span class="rail-item__name">{{ getFilterName(filter) }}</span>
              <strong>{{ filter.count }}</strong>
            </button>
          </aside>

          <section class="catalog-results" :aria-labelledby="resultsHeadingId">
            <header class="catalog-results__head">
              <div>
                <h2 :id="resultsHeadingId">{{ activeSectionTitle }}</h2>
                <p>{{ activeSectionDescription }}</p>
              </div>
              <span class="result-count">
                {{ catalogView.resultCount }}
                {{ t("attackScenarioLibrary.catalog.resultUnit") }}
              </span>
            </header>

            <div v-if="catalogView.results.length" class="result-list">
              <article
                v-for="evaluationItem in catalogView.results"
                :key="evaluationItem.evaluationItemId"
                class="dataset-result-card"
                :style="getEvaluationItemCardStyle(evaluationItem)"
              >
                <div class="dataset-result-card__main">
                  <div class="dataset-result-card__title-row">
                    <h3>{{ evaluationItem.name }}</h3>
                    <span class="dataset-result-card__sample">
                      {{ t("attackScenarioLibrary.labels.sampleCount") }}
                      <strong>
                        {{ formatSampleCount(evaluationItem.sampleCount ?? undefined) }}
                      </strong>
                    </span>
                  </div>

                  <span class="dataset-result-card__risk-domain">
                    <span aria-hidden="true"></span>
                    {{ evaluationItem.attackScenario.name }} / {{ evaluationItem.riskDomain.name }}
                  </span>

                  <p>
                    {{
                      evaluationItem.shortDescription ||
                      t("attackScenarioLibrary.subcategory.noDescription")
                    }}
                  </p>

                  <div class="dataset-result-card__meta">
                    <span>
                      {{ t("attackScenarioLibrary.labels.updatedAt") }}
                      {{ formatDateLabel(evaluationItem.updatedAt ?? undefined) }}
                    </span>
                  </div>
                </div>

                <div class="dataset-result-card__actions">
                  <UiButton
                    :to="
                      RouteLocation.evaluationItemDetail(
                        evaluationItem.evaluationItemId,
                      )
                    "
                    variant="text"
                    size="sm"
                  >
                    {{ t("attackScenarioLibrary.subcategory.viewDetails") }}
                  </UiButton>
                  <UiButton
                    variant="secondary"
                    size="sm"
                    @click="
                      handleSubmitClick(
                        evaluationItem.attackScenario.attackScenarioId,
                        evaluationItem.evaluationItemId,
                      )
                    "
                  >
                    {{
                      isLogin
                        ? t("attackScenarioLibrary.subcategory.useEvaluationItem")
                        : t("attackScenarioLibrary.subcategory.loginToEvaluate")
                    }}
                  </UiButton>
                </div>
              </article>
            </div>

            <PageStatePanel
              v-else
              :title="t('attackScenarioLibrary.pages.catalog.noMatchesTitle')"
              :message="t('attackScenarioLibrary.pages.catalog.noMatchesMessage')"
              :action-text="
                search.trim() ? t('attackScenarioLibrary.filter.clearSearch') : ''
              "
              @action="search = ''"
            />
          </section>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import { storeToRefs } from "pinia";
import { useRouter } from "vue-router";
import { RouteLocation } from "@/app/router/route-names";
import { useUserStore } from "@/modules/account/stores/userStore";
import { useAttackScenarioLibraryLocaleRefresh } from "@/modules/attack-scenario-library/composables/useAttackScenarioLibraryLocaleRefresh";
import {
  formatDateLabel,
  formatSampleCount,
  getAttackScenarioTheme,
  getRiskDomainTheme,
} from "@/modules/attack-scenario-library/lib/attack-scenario-library-utils";
import {
  ATTACK_SCENARIO_ALL_ID,
  RISK_DOMAIN_ALL_ID,
  buildAttackScenarioCatalogView,
  type AttackScenarioCatalogSortKey,
  type EvaluationItemCatalogResultItem,
  type RiskDomainFilterOption,
} from "@/modules/attack-scenario-library/model/attack-scenario-catalog-view";
import { useAttackScenarioCatalogStore } from "@/modules/attack-scenario-library/stores/attackScenarioCatalogStore";
import FormField from "@/shared/ui/forms/FormField.vue";
import UiButton from "@/shared/ui/actions/UiButton.vue";
import PageHero from "@/shared/ui/page/PageHero.vue";
import PageStatePanel from "@/shared/ui/feedback/PageStatePanel.vue";

const { locale, t } = useI18n();
const router = useRouter();
const attackScenarioCatalogStore = useAttackScenarioCatalogStore();
const userStore = useUserStore();
const { isLogin } = storeToRefs(userStore);
const { enabledAttackScenarios, loading, loaded, error } = storeToRefs(
  attackScenarioCatalogStore,
);

const resultsHeadingId = "dataset-catalog-heading";
const search = ref("");
const sortKey = ref<AttackScenarioCatalogSortKey>("samples-desc");
const activeAttackScenarioId = ref(ATTACK_SCENARIO_ALL_ID);
const activeRiskDomainId = ref(RISK_DOMAIN_ALL_ID);

const sortOptions = computed<
  Array<{ label: string; value: AttackScenarioCatalogSortKey }>
>(() => [
    {
      label: t("attackScenarioLibrary.filter.sortOptions.samplesDesc"),
      value: "samples-desc",
    },
    {
      label: t("attackScenarioLibrary.filter.sortOptions.updatedDesc"),
      value: "updated-desc",
    },
    {
      label: t("attackScenarioLibrary.filter.sortOptions.default"),
      value: "default",
    },
  ]);

const scenarioTabs = computed(() => [
  {
    attackScenarioId: ATTACK_SCENARIO_ALL_ID,
    name: t("attackScenarioLibrary.catalog.allCatalog"),
  },
  ...enabledAttackScenarios.value.map((scenario) => ({
    attackScenarioId: scenario.attackScenarioId,
    name: scenario.name,
  })),
]);

const catalogView = computed(() =>
  buildAttackScenarioCatalogView(
    enabledAttackScenarios.value,
    activeAttackScenarioId.value,
    activeRiskDomainId.value,
    search.value,
    sortKey.value,
  ),
);

const activeSectionTitle = computed(() =>
  catalogView.value.activeRiskDomain?.name ??
  catalogView.value.activeAttackScenario?.name ??
  t("attackScenarioLibrary.catalog.allCatalog"),
);

const activeSectionDescription = computed(() => {
  const riskDomain = catalogView.value.activeRiskDomain;
  const attackScenario = catalogView.value.activeAttackScenario;

  if (riskDomain) {
    return [riskDomain.meaning, riskDomain.description].filter(Boolean).join(" ");
  }

  if (attackScenario) {
    return attackScenario.description ?? "";
  }

  return t("attackScenarioLibrary.catalog.allCatalogDescription");
});

const reloadCatalog = async () => {
  await attackScenarioCatalogStore.fetchCatalog(true);
};

useAttackScenarioLibraryLocaleRefresh(locale, () =>
  attackScenarioCatalogStore.fetchCatalog(),
);

const handleSortKeyChange = (value: string) => {
  sortKey.value = value as AttackScenarioCatalogSortKey;
};

const handleAttackScenarioChange = (attackScenarioId: string) => {
  activeAttackScenarioId.value = attackScenarioId;
  activeRiskDomainId.value = RISK_DOMAIN_ALL_ID;
};

const handleSubmitClick = (
  attackScenarioId: string,
  evaluationItemId: string,
) => {
  if (!isLogin.value) {
    userStore.openLoginDialog();
    return;
  }

  void router.push({
    ...RouteLocation.agentSubmit,
    query: {
      attackScenarioId,
      evaluationItemIds: evaluationItemId,
    },
  });
};

const getFilterName = (filter: RiskDomainFilterOption): string =>
  filter.riskDomainId === RISK_DOMAIN_ALL_ID
    ? (catalogView.value.activeAttackScenario?.name ??
      t("attackScenarioLibrary.catalog.allCatalog"))
    : filter.name;

const cssVariablesFromTheme = (theme: ReturnType<typeof getAttackScenarioTheme>) => ({
  "--category-accent": theme.solid,
  "--category-soft": theme.soft,
  "--category-border": theme.border,
  "--category-text": theme.text,
});

const getScenarioTabStyle = (attackScenarioId: string) => {
  if (attackScenarioId === ATTACK_SCENARIO_ALL_ID) {
    return {
      "--category-accent": "var(--color-primary)",
      "--category-soft": "rgba(37, 99, 235, 0.08)",
      "--category-border": "rgba(37, 99, 235, 0.18)",
      "--category-text": "var(--color-primary)",
    };
  }

  return cssVariablesFromTheme(getAttackScenarioTheme(attackScenarioId));
};

const getFilterStyle = (filter: RiskDomainFilterOption) => {
  if (!filter.riskDomain || !filter.attackScenario) {
    return getScenarioTabStyle(
      filter.attackScenario?.attackScenarioId ?? ATTACK_SCENARIO_ALL_ID,
    );
  }

  return cssVariablesFromTheme(
    getRiskDomainTheme(
      filter.attackScenario.attackScenarioId,
      filter.riskDomain.riskDomainId,
      filter.attackScenario.riskDomains.map((riskDomain) => riskDomain.riskDomainId),
    ),
  );
};

const getEvaluationItemCardStyle = (item: EvaluationItemCatalogResultItem) => {
  return cssVariablesFromTheme(
    getRiskDomainTheme(
      item.attackScenario.attackScenarioId,
      item.riskDomain.riskDomainId,
      item.attackScenario.riskDomains.map((riskDomain) => riskDomain.riskDomainId),
    ),
  );
};

onMounted(async () => {
  await attackScenarioCatalogStore.fetchCatalog();
});
</script>

<style scoped lang="scss">
.attack-scenario-library-page {
  padding-bottom: 2.5rem;
}

.catalog-console {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 1rem;
}

.catalog-console__summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.85rem;
}

.summary-card {
  min-width: 0;
  padding: 1rem 1.05rem;
  border: 1px solid var(--color-border-soft);
  border-radius: var(--radius-card-sm);
  background: rgba(255, 255, 255, 0.78);
  box-shadow: var(--shadow-surface-soft);
}

.summary-card span {
  display: block;
  color: var(--color-text-subtle);
  font-size: 0.82rem;
  font-weight: 700;
  overflow-wrap: anywhere;
}

.summary-card strong {
  display: block;
  margin-top: 0.45rem;
  color: var(--color-text-dark);
  font-size: 1.35rem;
  line-height: 1.1;
  font-variant-numeric: tabular-nums;
  overflow-wrap: anywhere;
}

.catalog-console__controls {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(220px, 0.28fr);
  gap: 0.9rem;
  align-items: end;
}

.category-chip-strip {
  display: flex;
  gap: 0.55rem;
  overflow-x: auto;
  padding-bottom: 0.2rem;
  scrollbar-width: thin;
}

.category-chip {
  display: inline-flex;
  align-items: center;
  flex: 0 0 auto;
  min-height: 2.5rem;
  max-width: min(22rem, 78vw);
  gap: 0.55rem;
  padding: 0.55rem 0.82rem;
  border: 1px solid var(--category-border);
  border-radius: var(--radius-pill);
  background: rgba(255, 255, 255, 0.82);
  color: var(--category-text);
  cursor: pointer;
  font-weight: 700;
  transition:
    background var(--duration-fast) var(--ease-standard),
    border-color var(--duration-fast) var(--ease-standard),
    transform var(--duration-fast) var(--ease-standard);
}

.category-chip:hover,
.category-chip.active {
  background: var(--category-soft);
  border-color: var(--category-accent);
}

.category-chip:hover {
  transform: translateY(-1px);
}

.category-chip span {
  min-width: 0;
  overflow-wrap: anywhere;
}

.catalog-console__body {
  display: grid;
  grid-template-columns: minmax(210px, 0.26fr) minmax(0, 1fr);
  gap: 1.1rem;
  align-items: start;
}

.category-rail {
  position: sticky;
  top: calc(var(--nav-height) + 1rem);
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 0.35rem;
  padding: 0.65rem;
  border: 1px solid var(--color-border-soft);
  border-radius: var(--radius-card-sm);
  background: rgba(255, 255, 255, 0.72);
  box-shadow: var(--shadow-surface-soft);
}

.rail-item {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  min-height: 2.55rem;
  gap: 0.55rem;
  padding: 0.55rem 0.65rem;
  border: 1px solid transparent;
  border-radius: 0.85rem;
  background: transparent;
  color: var(--color-text-muted);
  cursor: pointer;
  text-align: left;
  transition:
    background var(--duration-fast) var(--ease-standard),
    border-color var(--duration-fast) var(--ease-standard),
    color var(--duration-fast) var(--ease-standard);
}

.rail-item:hover,
.rail-item.active {
  background: var(--category-soft);
  border-color: var(--category-border);
  color: var(--category-text);
}

.rail-item__dot {
  width: 0.48rem;
  height: 0.48rem;
  border-radius: var(--radius-circle);
  background: var(--category-accent);
}

.rail-item__name {
  min-width: 0;
  font-weight: 700;
  overflow-wrap: anywhere;
}

.rail-item strong {
  font-variant-numeric: tabular-nums;
}

.catalog-results {
  min-width: 0;
}

.catalog-results__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  padding: 1rem 0 0.85rem;
  border-top: 1px solid var(--color-border-soft);
}

.catalog-results__head > div {
  min-width: 0;
}

.catalog-results__head h2 {
  margin: 0;
  color: var(--color-text-dark);
  font-size: 1.28rem;
  overflow-wrap: anywhere;
}

.catalog-results__head p {
  margin: 0.4rem 0 0;
  max-width: 72ch;
  color: var(--color-text-muted);
  line-height: 1.68;
  overflow-wrap: anywhere;
}

.result-count {
  flex-shrink: 0;
  align-self: flex-start;
  padding: 0.42rem 0.72rem;
  border: 1px solid var(--color-border-soft);
  border-radius: var(--radius-pill);
  background: rgba(255, 255, 255, 0.76);
  color: var(--color-text-subtle);
  font-size: 0.84rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.result-list {
  display: flex;
  flex-direction: column;
  gap: 0.72rem;
}

.dataset-result-card {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(11rem, auto);
  gap: 1.1rem;
  min-width: 0;
  padding: 1.05rem 1.1rem 1.05rem 1.25rem;
  border: 1px solid var(--color-border-soft);
  border-radius: var(--radius-card-sm);
  background: rgba(255, 255, 255, 0.86);
  box-shadow: var(--shadow-surface-soft);
  transition:
    border-color var(--duration-fast) var(--ease-standard),
    box-shadow var(--duration-fast) var(--ease-standard),
    transform var(--duration-fast) var(--ease-standard);
}

.dataset-result-card::before {
  content: "";
  position: absolute;
  inset: 0 auto 0 0;
  width: 4px;
  border-radius: var(--radius-card-sm) 0 0 var(--radius-card-sm);
  background: var(--category-accent);
}

.dataset-result-card:hover {
  transform: translateY(-1px);
  border-color: var(--category-border);
  box-shadow: var(--shadow-surface-hover);
}

.dataset-result-card__main {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.6rem;
  min-width: 0;
}

.dataset-result-card__title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.85rem;
  min-width: 0;
}

.dataset-result-card h3 {
  min-width: 0;
  margin: 0;
  color: var(--color-text-dark);
  font-size: 1.1rem;
  line-height: 1.35;
  overflow-wrap: anywhere;
}

.dataset-result-card__sample {
  flex-shrink: 0;
  color: var(--color-text-subtle);
  font-size: 0.82rem;
  font-weight: 700;
  white-space: nowrap;
}

.dataset-result-card__sample strong {
  color: var(--category-text);
  font-variant-numeric: tabular-nums;
}

.dataset-result-card__risk-domain {
  display: inline-flex;
  align-items: center;
  max-width: 100%;
  gap: 0.45rem;
  padding: 0.38rem 0.62rem;
  border: 1px solid var(--category-border);
  border-radius: var(--radius-pill);
  background: var(--category-soft);
  color: var(--category-text);
  font-size: 0.95rem;
  font-weight: 850;
  line-height: 1.25;
  overflow-wrap: anywhere;
}

.dataset-result-card__risk-domain span {
  flex: 0 0 auto;
  width: 0.52rem;
  height: 0.52rem;
  border-radius: var(--radius-circle);
  background: var(--category-accent);
}

.dataset-result-card p {
  margin: 0;
  color: var(--color-text-muted);
  line-height: 1.7;
  overflow-wrap: anywhere;
}

.dataset-result-card__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem 0.8rem;
  color: var(--color-text-subtle);
  font-size: 0.84rem;
  font-weight: 600;
}

.dataset-result-card__actions {
  display: flex;
  align-self: center;
  align-items: center;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 0.55rem;
  min-width: 10rem;
}

.dataset-result-card__actions :deep(a),
.dataset-result-card__actions :deep(button) {
  min-width: 0;
}

@media (max-width: 1100px) {
  .catalog-console__summary {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .catalog-console__body {
    grid-template-columns: 1fr;
  }

  .category-rail {
    display: none;
  }
}

@media (max-width: 768px) {
  .catalog-console__summary,
  .catalog-console__controls {
    grid-template-columns: 1fr;
  }

  .catalog-results__head,
  .dataset-result-card,
  .dataset-result-card__title-row {
    flex-direction: column;
  }

  .catalog-results__head {
    display: flex;
  }

  .dataset-result-card {
    display: flex;
  }

  .dataset-result-card__sample {
    white-space: normal;
  }

  .dataset-result-card__actions {
    width: 100%;
    min-width: 0;
    justify-content: stretch;
  }

  .dataset-result-card__actions :deep(a),
  .dataset-result-card__actions :deep(button) {
    flex: 1 1 10rem;
  }
}
</style>
