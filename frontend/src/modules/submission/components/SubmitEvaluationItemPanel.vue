<template>
  <SectionBlock
    :title="t('submission.evaluationItems.title')"
    :description="t('submission.evaluationItems.description')"
  >
    <template #actions>
      <UiButton
        variant="secondary"
        size="sm"
        :disabled="!selectedAttackScenarioId || !riskDomains.length"
        @click="$emit('select-all')"
      >
        {{ t("submission.actions.selectAll") }}
      </UiButton>
      <UiButton
        variant="secondary"
        size="sm"
        :disabled="!selectedEvaluationItemIds.length"
        @click="$emit('clear-all')"
      >
        {{ t("submission.actions.clear") }}
      </UiButton>
    </template>

    <div class="toolbar">
      <FormField
        :label="t('submission.evaluationItems.attackScenarioLabel')"
        :model-value="selectedAttackScenarioId"
        type="select"
        :options="attackScenarioOptions"
        :placeholder="t('submission.evaluationItems.attackScenarioPlaceholder')"
        leading-icon="app:attackScenarioLibrary.catalog"
        @update:model-value="$emit('update:attack-scenario-id', $event)"
      />
      <FormField
        :label="t('submission.evaluationItems.searchLabel')"
        :model-value="search"
        type="search"
        :placeholder="t('submission.evaluationItems.searchPlaceholder')"
        leading-icon="app:action.search"
        @update:model-value="search = $event.trim()"
      />

      <div class="toolbar-metrics">
        <span>{{ t("submission.evaluationItems.selectedRiskDomains", { count: selectedCategoryCount }) }}</span>
        <span>{{ t("submission.evaluationItems.selectedEvaluationItems", { count: selectedEvaluationItemIds.length }) }}</span>
        <span>{{ t("submission.evaluationItems.currentResults", { count: visibleEvaluationItemCount }) }}</span>
      </div>
    </div>

    <div class="status-list">
      <InlineNotice
        v-if="selectionErrorMessage"
        tone="danger"
        :message="selectionErrorMessage"
      />
      <InlineNotice
        v-if="status === 'refreshing'"
        tone="info"
        :message="t('submission.evaluationItems.refreshing')"
      />
      <PageStatePanel
        v-if="status === 'ready' && !selectedAttackScenarioId"
        :title="t('submission.evaluationItems.attackScenarioRequiredTitle')"
        :message="t('submission.evaluationItems.attackScenarioRequiredMessage')"
      />
      <PageStatePanel
        v-else-if="status === 'loading' && !riskDomains.length"
        :title="t('submission.evaluationItems.loadingTitle')"
        :message="t('submission.evaluationItems.loadingMessage')"
        :loading="true"
      />
      <PageStatePanel
        v-else-if="status === 'error' && !riskDomains.length"
        :title="t('submission.evaluationItems.loadFailedTitle')"
        :message="errorMessage || t('submission.evaluationItems.retrySubmit')"
        :action-text="t('common.actions.retry')"
        action-variant="secondary"
        @action="$emit('retry')"
      />
      <PageStatePanel
        v-else-if="status === 'empty'"
        :title="t('submission.evaluationItems.emptyTitle')"
        :message="t('submission.evaluationItems.emptyMessage')"
      />
      <PageStatePanel
        v-else-if="status === 'ready' && selectedAttackScenarioId && !riskDomains.length"
        :title="t('submission.evaluationItems.attackScenarioEmptyTitle')"
        :message="t('submission.evaluationItems.attackScenarioEmptyMessage')"
      />
      <InlineNotice
        v-else-if="status === 'error'"
        tone="danger"
        :message="errorMessage || t('submission.evaluationItems.refreshFailed')"
      >
        <template #actions>
          <UiButton variant="text" size="sm" @click="$emit('retry')">
            {{ t("submission.actions.reload") }}
          </UiButton>
        </template>
      </InlineNotice>
    </div>

    <template v-if="filteredRiskDomains.length">
      <SubmitRiskDomainList
        :attack-scenario="selectedAttackScenario"
        :risk-domains="filteredRiskDomains"
        :selected-evaluation-item-ids="selectedEvaluationItemIds"
        :expanded-risk-domain-ids="expandedRiskDomainIds"
        @toggle-risk-domain="$emit('toggle-risk-domain', $event)"
        @toggle-evaluation-item="$emit('toggle-evaluation-item', $event)"
        @toggle-expanded="$emit('toggle-expanded', $event)"
      />
    </template>

    <PageStatePanel
      v-else-if="riskDomains.length && status !== 'loading'"
      :title="t('submission.evaluationItems.noMatchesTitle')"
      :message="t('submission.evaluationItems.clearSearchMessage')"
    />
  </SectionBlock>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { useI18n } from "vue-i18n";
import SubmitRiskDomainList from "@/modules/submission/components/SubmitRiskDomainList.vue";
import type {
  AttackScenarioCatalogItem,
  RiskDomainCatalogItem,
} from "@/shared/types/attack-scenario-library-types";
import type { SubmitAttackScenarioCatalogStatus } from "@/modules/submission/composables/useSubmitAttackScenarioCatalog";
import FormField from "@/shared/ui/forms/FormField.vue";
import InlineNotice from "@/shared/ui/feedback/InlineNotice.vue";
import PageStatePanel from "@/shared/ui/feedback/PageStatePanel.vue";
import SectionBlock from "@/shared/ui/page/SectionBlock.vue";
import UiButton from "@/shared/ui/actions/UiButton.vue";

const props = defineProps<{
  attackScenarios: AttackScenarioCatalogItem[];
  selectedAttackScenario: AttackScenarioCatalogItem | null;
  selectedAttackScenarioId: string;
  riskDomains: RiskDomainCatalogItem[];
  selectedEvaluationItemIds: string[];
  expandedRiskDomainIds: string[];
  status: SubmitAttackScenarioCatalogStatus;
  errorMessage?: string;
  selectionErrorMessage?: string;
}>();

defineEmits<{
  (event: "update:attack-scenario-id", attackScenarioId: string): void;
  (event: "select-all"): void;
  (event: "clear-all"): void;
  (event: "toggle-risk-domain", riskDomainId: string): void;
  (event: "toggle-evaluation-item", evaluationItemId: string): void;
  (event: "toggle-expanded", riskDomainId: string): void;
  (event: "retry"): void;
}>();

const search = ref("");
const { t } = useI18n();

const attackScenarioOptions = computed(() =>
  props.attackScenarios.map((scenario) => ({
    label: scenario.name,
    value: scenario.attackScenarioId,
  })),
);

const matchesSearch = (riskDomain: RiskDomainCatalogItem, keyword: string) => {
  if (!keyword) {
    return true;
  }

  const normalized = keyword.toLowerCase();
  const riskDomainMatched = [
    riskDomain.name,
    riskDomain.meaning ?? "",
    riskDomain.description ?? "",
  ].some((value) => value.toLowerCase().includes(normalized));

  if (riskDomainMatched) {
    return true;
  }

  return riskDomain.evaluationItems.some((evaluationItem) =>
    [evaluationItem.name, evaluationItem.shortDescription ?? ""].some((value) =>
      value.toLowerCase().includes(normalized),
    ),
  );
};

const filteredRiskDomains = computed(() => {
  const keyword = search.value.trim().toLowerCase();

  return props.riskDomains
    .filter((riskDomain) => matchesSearch(riskDomain, keyword))
    .map((riskDomain) => ({
      ...riskDomain,
      evaluationItems: riskDomain.evaluationItems.filter((evaluationItem) => {
        if (!keyword) {
          return true;
        }

        return [
          riskDomain.name,
          riskDomain.meaning ?? "",
          evaluationItem.name,
          evaluationItem.shortDescription ?? "",
        ].some((value) => value.toLowerCase().includes(keyword));
      }),
    }))
    .filter((riskDomain) => riskDomain.evaluationItems.length > 0);
});

const visibleEvaluationItemCount = computed(() =>
  filteredRiskDomains.value.reduce(
    (count, riskDomain) => count + riskDomain.evaluationItems.length,
    0,
  ),
);

const selectedCategoryCount = computed(
  () =>
    props.riskDomains.filter((riskDomain) =>
      riskDomain.evaluationItems.some((item) =>
        props.selectedEvaluationItemIds.includes(item.evaluationItemId),
      ),
    ).length,
);
</script>

<style scoped lang="scss">
.toolbar {
  display: grid;
  grid-template-columns: minmax(240px, 1.4fr) minmax(0, 1fr);
  gap: 0.85rem;
  min-width: 0;
}

.toolbar-metrics {
  display: flex;
  flex-wrap: wrap;
  align-items: end;
  justify-content: flex-end;
  gap: 0.75rem;
  min-width: 0;
  color: var(--color-text-muted);
  font-size: 0.9rem;
}

.toolbar-metrics > * {
  min-width: 0;
}

.status-list {
  display: flex;
  flex-direction: column;
  gap: 0.7rem;
}

@media (max-width: 768px) {
  .toolbar {
    grid-template-columns: 1fr;
  }

  .toolbar-metrics {
    width: 100%;
    justify-content: flex-start;
  }
}
</style>
