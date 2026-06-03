<template>
  <div class="category-list">
    <SubmitRiskDomainBlock
      v-for="riskDomain in riskDomains"
      :key="riskDomain.riskDomainId"
      :risk-domain="riskDomain"
      :theme="resolveRiskDomainTheme(riskDomain.riskDomainId)"
      :selected-evaluation-item-ids="selectedEvaluationItemIds"
      :expanded="expandedRiskDomainIds.includes(riskDomain.riskDomainId)"
      @toggle-risk-domain="$emit('toggle-risk-domain', $event)"
      @toggle-evaluation-item="$emit('toggle-evaluation-item', $event)"
      @toggle-expanded="$emit('toggle-expanded', $event)"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { getRiskDomainTheme } from "@/modules/attack-scenario-library/lib/attack-scenario-library-utils";
import SubmitRiskDomainBlock from "@/modules/submission/components/SubmitRiskDomainBlock.vue";
import type {
  AttackScenarioCatalogItem,
  RiskDomainCatalogItem,
} from "@/shared/types/attack-scenario-library-types";

const props = defineProps<{
  attackScenario: AttackScenarioCatalogItem | null;
  riskDomains: RiskDomainCatalogItem[];
  selectedEvaluationItemIds: string[];
  expandedRiskDomainIds: string[];
}>();

defineEmits<{
  (event: "toggle-risk-domain", riskDomainId: string): void;
  (event: "toggle-evaluation-item", evaluationItemId: string): void;
  (event: "toggle-expanded", riskDomainId: string): void;
}>();

const riskDomainThemeIds = computed(() =>
  props.riskDomains.map((riskDomain) => riskDomain.riskDomainId),
);

const resolveRiskDomainTheme = (riskDomainId: string) =>
  getRiskDomainTheme(
    props.attackScenario?.attackScenarioId ?? "",
    riskDomainId,
    riskDomainThemeIds.value,
  );
</script>

<style scoped lang="scss">
.category-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
</style>
