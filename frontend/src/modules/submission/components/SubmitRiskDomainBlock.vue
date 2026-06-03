<template>
  <article class="category-block" :style="riskDomainBlockStyle">
    <div class="category-row">
      <label class="category-main">
        <input
          type="checkbox"
          class="selection-input"
          :checked="isFullySelected"
          @change="$emit('toggle-risk-domain', riskDomain.riskDomainId)"
        />
        <span
          class="selection-box"
          :class="{
            'selection-box--checked': isFullySelected,
            'selection-box--partial': isPartiallySelected,
          }"
          aria-hidden="true"
        >
          <AppIcon
            v-if="isFullySelected"
            icon="app:action.select"
            class="selection-box-icon"
          />
          <span v-else-if="isPartiallySelected" class="selection-box-dash"></span>
        </span>
        <div class="category-copy">
          <span class="category-name">{{ riskDomain.name }}</span>
          <span v-if="riskDomain.meaning" class="category-meaning">
            {{ riskDomain.meaning }}
          </span>
        </div>
      </label>

      <div class="category-right">
        <span class="category-count">
          {{ t("submission.evaluationItems.categoryCount", { count: riskDomain.evaluationItems.length }) }}
        </span>
        <button
          class="expand-btn"
          type="button"
          :aria-label="expanded ? t('submission.evaluationItems.collapse') : t('submission.evaluationItems.expand')"
          :title="expanded ? t('submission.evaluationItems.collapse') : t('submission.evaluationItems.expand')"
          @click="$emit('toggle-expanded', riskDomain.riskDomainId)"
        >
          <AppIcon
            :icon="expanded ? 'app:control.collapse' : 'app:control.expand'"
            class="expand-btn-icon"
          />
        </button>
      </div>
    </div>

    <div v-if="expanded" class="evaluation-item-list">
      <label
        v-for="evaluationItem in riskDomain.evaluationItems"
        :key="evaluationItem.evaluationItemId"
        class="evaluation-item"
      >
        <input
          type="checkbox"
          class="selection-input"
          :checked="selectedEvaluationItemIds.includes(evaluationItem.evaluationItemId)"
          @change="$emit('toggle-evaluation-item', evaluationItem.evaluationItemId)"
        />
        <span
          class="selection-box"
          :class="{
            'selection-box--checked': selectedEvaluationItemIds.includes(evaluationItem.evaluationItemId),
          }"
          aria-hidden="true"
        >
          <AppIcon
            v-if="selectedEvaluationItemIds.includes(evaluationItem.evaluationItemId)"
            icon="app:action.select"
            class="selection-box-icon"
          />
        </span>
        <div class="evaluation-item-copy">
          <span class="evaluation-item-name">{{ evaluationItem.name }}</span>
          <span class="evaluation-item-description">
            {{ evaluationItem.shortDescription || t("submission.evaluationItems.noDescription") }}
          </span>
        </div>
      </label>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import type { ScenarioTheme } from "@/modules/attack-scenario-library/lib/attack-scenario-library-utils";
import type { RiskDomainCatalogItem } from "@/shared/types/attack-scenario-library-types";
import AppIcon from "@/shared/ui/branding/AppIcon.vue";

const props = defineProps<{
  riskDomain: RiskDomainCatalogItem;
  theme: ScenarioTheme;
  selectedEvaluationItemIds: string[];
  expanded: boolean;
}>();

const { t } = useI18n();

defineEmits<{
  (event: "toggle-risk-domain", riskDomainId: string): void;
  (event: "toggle-evaluation-item", evaluationItemId: string): void;
  (event: "toggle-expanded", riskDomainId: string): void;
}>();

const isFullySelected = computed(() =>
  props.riskDomain.evaluationItems.every((item) =>
    props.selectedEvaluationItemIds.includes(item.evaluationItemId),
  ),
);

const isPartiallySelected = computed(() => {
  const selectedCount = props.riskDomain.evaluationItems.filter((item) =>
    props.selectedEvaluationItemIds.includes(item.evaluationItemId),
  ).length;

  return selectedCount > 0 && selectedCount < props.riskDomain.evaluationItems.length;
});

const riskDomainBlockStyle = computed(() => {
  const theme = props.theme;

  return {
    "--category-soft": theme.soft,
    "--category-border": theme.border,
    "--category-text": theme.text,
    "--category-gradient": theme.gradient,
    "--category-shadow": theme.shadow,
  };
});
</script>

<style scoped lang="scss">
.category-block {
  overflow: hidden;
  border: 1px solid var(--category-border, #e2e8f0);
  border-radius: 1.3rem;
  box-shadow: 0 12px 24px -28px var(--category-shadow, rgba(15, 23, 42, 0.22));
}

.category-block::before {
  display: block;
  height: 3px;
  background: var(
    --category-gradient,
    linear-gradient(135deg, #2563eb, #7c3aed)
  );
  content: "";
}

.category-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 1rem 1.05rem;
  background: linear-gradient(180deg, var(--category-soft, #f8fafc), #ffffff 88%);
}

.category-main {
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: 0.8rem;
  min-width: 0;
}

.selection-input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.selection-box {
  display: inline-flex;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  width: 1.15rem;
  height: 1.15rem;
  margin-top: 0.08rem;
  border: 1px solid rgba(148, 163, 184, 0.34);
  border-radius: 0.34rem;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.82);
  transition:
    background var(--duration-fast) var(--ease-standard),
    border-color var(--duration-fast) var(--ease-standard),
    box-shadow var(--duration-fast) var(--ease-standard);
}

.selection-box--checked,
.selection-box--partial {
  border-color: rgba(37, 99, 235, 0.92);
  background: linear-gradient(
    135deg,
    rgba(37, 99, 235, 0.98),
    rgba(59, 130, 246, 0.94)
  );
  box-shadow: 0 8px 18px -14px rgba(37, 99, 235, 0.74);
}

.selection-box-icon {
  width: 0.82rem;
  height: 0.82rem;
  color: #ffffff;
}

.selection-box-dash {
  width: 0.56rem;
  height: 0.12rem;
  border-radius: 999px;
  background: #ffffff;
}

.category-copy,
.evaluation-item-copy {
  display: flex;
  min-width: 0;
  flex-direction: column;
}

.category-copy {
  gap: 0.24rem;
}

.category-name {
  color: var(--color-text-dark);
  font-weight: 700;
}

.category-meaning {
  color: var(--category-text, #475569);
  font-size: 0.9rem;
}

.category-right {
  display: inline-flex;
  align-items: center;
  gap: 0.75rem;
}

.category-count {
  color: var(--color-text-subtle);
  font-size: 0.88rem;
}

.expand-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.35rem;
  height: 2.35rem;
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 10px 20px -18px rgba(15, 23, 42, 0.32);
  color: var(--category-text, #334155);
  cursor: pointer;
  transition:
    transform var(--duration-fast) var(--ease-standard),
    box-shadow var(--duration-fast) var(--ease-standard),
    background var(--duration-fast) var(--ease-standard);
}

.expand-btn:hover {
  box-shadow: 0 12px 22px -18px rgba(15, 23, 42, 0.36);
  transform: translateY(-1px);
}

.expand-btn-icon {
  width: 1rem;
  height: 1rem;
}

.evaluation-item-list {
  display: flex;
  flex-direction: column;
  padding: 0.15rem 1.05rem 0.9rem;
  background: rgba(248, 250, 252, 0.46);
}

.evaluation-item {
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: 0.7rem;
  min-height: 3.5rem;
  padding: 0.78rem 0.2rem;
  cursor: pointer;
}

.evaluation-item + .evaluation-item {
  border-top: 1px solid rgba(148, 163, 184, 0.16);
}

.evaluation-item:hover .evaluation-item-name {
  color: var(--category-text, var(--color-primary));
}

.evaluation-item:focus-within {
  outline: 2px solid rgba(37, 99, 235, 0.24);
  outline-offset: -2px;
}

.evaluation-item-copy {
  gap: 0.28rem;
}

.evaluation-item-name {
  color: var(--color-text-dark);
  font-weight: 600;
}

.evaluation-item-description {
  color: var(--color-text-subtle);
  line-height: 1.65;
}

@media (max-width: 768px) {
  .category-right {
    width: 100%;
    justify-content: flex-start;
  }

  .category-row {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
