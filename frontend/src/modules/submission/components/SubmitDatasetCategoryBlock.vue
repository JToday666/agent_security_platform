<template>
  <article class="category-block" :style="categoryBlockStyle">
    <div class="category-row">
      <label class="category-main">
        <input
          type="checkbox"
          class="selection-input"
          :checked="isFullySelected"
          @change="$emit('toggle-category', category.categoryId)"
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
          <span class="category-name">{{ category.name }}</span>
          <span v-if="category.meaning" class="category-meaning">
            {{ category.meaning }}
          </span>
        </div>
      </label>

      <div class="category-right">
        <span class="category-count">
          {{ t("submission.dataset.categoryCount", { count: category.subcategories.length }) }}
        </span>
        <button
          class="expand-btn"
          type="button"
          :aria-label="expanded ? t('submission.dataset.collapse') : t('submission.dataset.expand')"
          :title="expanded ? t('submission.dataset.collapse') : t('submission.dataset.expand')"
          @click="$emit('toggle-expanded', category.categoryId)"
        >
          <AppIcon
            :icon="expanded ? 'app:control.collapse' : 'app:control.expand'"
            class="expand-btn-icon"
          />
        </button>
      </div>
    </div>

    <div v-if="expanded" class="dataset-list">
      <label
        v-for="dataset in category.subcategories"
        :key="dataset.datasetId"
        class="dataset-item"
      >
        <input
          type="checkbox"
          class="selection-input"
          :checked="selectedDatasetIds.includes(dataset.datasetId)"
          @change="$emit('toggle-dataset', dataset.datasetId)"
        />
        <span
          class="selection-box"
          :class="{
            'selection-box--checked': selectedDatasetIds.includes(dataset.datasetId),
          }"
          aria-hidden="true"
        >
          <AppIcon
            v-if="selectedDatasetIds.includes(dataset.datasetId)"
            icon="app:action.select"
            class="selection-box-icon"
          />
        </span>
        <div class="dataset-copy">
          <span class="dataset-name">{{ dataset.name }}</span>
          <span class="dataset-description">
            {{ dataset.shortDescription || t("submission.dataset.noDescription") }}
          </span>
        </div>
      </label>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import {
  getCategoryTheme,
  isCategoryFullySelected,
} from "@/modules/dataset/lib/dataset-utils";
import type { DatasetCategory } from "@/shared/types/dataset-types";
import AppIcon from "@/shared/ui/branding/AppIcon.vue";

const props = defineProps<{
  category: DatasetCategory;
  selectedDatasetIds: string[];
  expanded: boolean;
}>();

const { t } = useI18n();

defineEmits<{
  (event: "toggle-category", categoryId: string): void;
  (event: "toggle-dataset", datasetId: string): void;
  (event: "toggle-expanded", categoryId: string): void;
}>();

const isFullySelected = computed(() =>
  isCategoryFullySelected(props.category, props.selectedDatasetIds),
);

const isPartiallySelected = computed(() => {
  const selectedCount = props.category.subcategories.filter((item) =>
    props.selectedDatasetIds.includes(item.datasetId),
  ).length;

  return selectedCount > 0 && selectedCount < props.category.subcategories.length;
});

const categoryBlockStyle = computed(() => {
  const theme = getCategoryTheme(props.category.categoryId);

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
.dataset-copy {
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

.dataset-list {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
  padding: 0 1.05rem 1rem;
}

.dataset-item {
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: 0.7rem;
  padding: 0.85rem 0.9rem;
  border: 1px solid rgba(148, 163, 184, 0.14);
  border-radius: 1rem;
  background: rgba(255, 255, 255, 0.78);
}

.dataset-copy {
  gap: 0.28rem;
}

.dataset-name {
  color: var(--color-text-dark);
  font-weight: 600;
}

.dataset-description {
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
