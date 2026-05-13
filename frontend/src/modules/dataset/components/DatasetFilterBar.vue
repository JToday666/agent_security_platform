<template>
  <SectionBlock
    :title="t('dataset.filter.title')"
    :description="t('dataset.filter.description')"
  >
    <div class="toolbar">
      <FormField
        :label="t('dataset.filter.searchLabel')"
        :model-value="search"
        type="search"
        :placeholder="t('dataset.filter.searchPlaceholder')"
        leading-icon="app:action.search"
        appearance="soft"
        @update:model-value="$emit('update:search', $event)"
      />

      <FormField
        :label="t('dataset.filter.sortLabel')"
        :model-value="sortKey"
        type="select"
        :options="sortOptions"
        leading-icon="app:action.sort"
        appearance="soft"
        @update:model-value="handleSortKeyChange"
      />

      <UiButton
        class="clear-btn"
        variant="secondary"
        leading-icon="app:action.reset"
        :disabled="!search.trim()"
        @click="$emit('clear-search')"
      >
        {{ t("dataset.filter.clearSearch") }}
      </UiButton>
    </div>

    <div class="chip-row">
      <button
        v-for="category in categories"
        :key="category.categoryId"
        type="button"
        class="category-chip"
        :class="{ active: activeCategoryId === category.categoryId }"
        :style="getChipStyle(category.categoryId, activeCategoryId === category.categoryId)"
        @click="$emit('select-category', category.categoryId)"
      >
        <span class="chip-name">{{ category.name }}</span>
      </button>
    </div>
  </SectionBlock>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import { getCategoryTheme } from "@/modules/dataset/lib/dataset-utils";
import type { DatasetCatalogSortKey } from "@/modules/dataset/model/dataset-catalog-view";
import FormField from "@/shared/ui/forms/FormField.vue";
import UiButton from "@/shared/ui/actions/UiButton.vue";
import SectionBlock from "@/shared/ui/page/SectionBlock.vue";
import type { DatasetCategoryViewModel } from "@/shared/types/dataset-types";

const emit = defineEmits<{
  (event: "select-category", categoryId: string): void;
  (event: "update:search", value: string): void;
  (event: "update:sortKey", value: DatasetCatalogSortKey): void;
  (event: "clear-search"): void;
}>();

defineProps<{
  categories: DatasetCategoryViewModel[];
  activeCategoryId: string;
  search: string;
  sortKey: DatasetCatalogSortKey;
}>();

const { t } = useI18n();

const sortOptions = computed<Array<{ label: string; value: DatasetCatalogSortKey }>>(
  () => [
    { label: t("dataset.filter.sortOptions.default"), value: "default" },
    {
      label: t("dataset.filter.sortOptions.updatedDesc"),
      value: "updated-desc",
    },
    {
      label: t("dataset.filter.sortOptions.samplesDesc"),
      value: "samples-desc",
    },
  ],
);

const handleSortKeyChange = (value: string) => {
  emit("update:sortKey", value as DatasetCatalogSortKey);
};

const getChipStyle = (categoryId: string, active: boolean) => {
  const theme = getCategoryTheme(categoryId);

  if (active) {
    return {
      background: theme.gradient,
      color: "#ffffff",
      border: `1px solid ${theme.solid}`,
      boxShadow: `0 16px 28px -26px ${theme.shadow}`,
    };
  }

  return {
    background: "rgba(255, 255, 255, 0.82)",
    color: theme.text,
    border: `1px solid ${theme.border}`,
    boxShadow: `0 12px 20px -24px ${theme.shadow}`,
  };
};
</script>

<style scoped lang="scss">
.toolbar {
  display: grid;
  grid-template-columns: minmax(240px, 1.4fr) minmax(220px, 0.92fr) auto;
  gap: 0.95rem;
}

.clear-btn {
  align-self: end;
}

.chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.8rem;
  min-width: 0;
}

.category-chip {
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.55rem;
  max-width: 100%;
  min-width: 0;
  padding: 0.82rem 1.05rem;
  border-radius: var(--radius-pill);
  overflow-wrap: anywhere;
  cursor: pointer;
  transition: transform var(--duration-fast) var(--ease-standard);
}

.category-chip:hover {
  transform: translateY(-1px);
}

.chip-name {
  min-width: 0;
  font-weight: 700;
  overflow-wrap: anywhere;
}

@media (max-width: 900px) {
  .toolbar {
    grid-template-columns: 1fr 1fr;
  }

  .clear-btn {
    grid-column: 1 / -1;
  }
}

@media (max-width: 768px) {
  .toolbar {
    grid-template-columns: 1fr;
  }

  .clear-btn {
    width: 100%;
  }
}
</style>
