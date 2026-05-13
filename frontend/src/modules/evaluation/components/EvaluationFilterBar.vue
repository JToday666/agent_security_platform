<template>
  <SectionBlock
    :title="t('evaluation.filter.title')"
    :description="t('evaluation.filter.description')"
  >
    <div class="filter-grid">
      <FormField
        :label="t('evaluation.filter.search')"
        :model-value="search"
        type="search"
        :placeholder="t('evaluation.filter.placeholder')"
        leading-icon="app:action.search"
        appearance="soft"
        @update:model-value="$emit('update:search', $event)"
      />

      <FormField
        :label="t('evaluation.filter.status')"
        :model-value="status"
        type="select"
        :options="statusOptions"
        leading-icon="app:filter.status"
        appearance="soft"
        @update:model-value="handleStatusChange"
      />

      <FormField
        :label="t('evaluation.filter.visibility')"
        :model-value="visibility"
        type="select"
        :options="visibilityOptions"
        leading-icon="app:filter.visibility"
        appearance="soft"
        @update:model-value="handleVisibilityChange"
      />

      <FormField
        :label="t('evaluation.filter.submitMethod')"
        :model-value="submitMethod"
        type="select"
        :options="methodOptions"
        leading-icon="app:field.submitMethod"
        appearance="soft"
        @update:model-value="handleSubmitMethodChange"
      />
    </div>
  </SectionBlock>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import type {
  EvaluationRecordFilterMethod,
  EvaluationRecordFilterStatus,
  EvaluationRecordFilterVisibility,
} from "@/modules/evaluation/lib/evaluation-record-filters";
import FormField from "@/shared/ui/forms/FormField.vue";
import SectionBlock from "@/shared/ui/page/SectionBlock.vue";

defineProps<{
  search: string;
  status: EvaluationRecordFilterStatus;
  visibility: EvaluationRecordFilterVisibility;
  submitMethod: EvaluationRecordFilterMethod;
}>();

const emit = defineEmits<{
  (event: "update:search", value: string): void;
  (event: "update:status", value: EvaluationRecordFilterStatus): void;
  (event: "update:visibility", value: EvaluationRecordFilterVisibility): void;
  (event: "update:submitMethod", value: EvaluationRecordFilterMethod): void;
}>();
const { t } = useI18n();

const statusOptions = computed<Array<{
  label: string;
  value: EvaluationRecordFilterStatus;
}>>(() => [
  { label: t("evaluation.filter.statusAll"), value: "all" },
  { label: t("evaluation.status.pending"), value: "pending" },
  { label: t("evaluation.status.running"), value: "running" },
  { label: t("evaluation.status.paused"), value: "paused" },
  { label: t("evaluation.status.completed"), value: "completed" },
  { label: t("evaluation.status.failed"), value: "failed" },
  { label: t("evaluation.status.canceled"), value: "canceled" },
  { label: t("evaluation.status.terminated"), value: "terminated" },
]);

const visibilityOptions = computed<Array<{
  label: string;
  value: EvaluationRecordFilterVisibility;
}>>(() => [
  { label: t("evaluation.filter.visibilityAll"), value: "all" },
  { label: t("common.status.public"), value: "public" },
  { label: t("common.status.anonymous"), value: "anonymous" },
  { label: t("common.status.rankedOut"), value: "unranked" },
]);

const methodOptions = computed<Array<{
  label: string;
  value: EvaluationRecordFilterMethod;
}>>(() => [
  { label: t("evaluation.filter.methodAll"), value: "all" },
  { label: "API", value: "api" },
  { label: "Docker", value: "docker" },
]);

const handleStatusChange = (value: string) => {
  emit("update:status", value as EvaluationRecordFilterStatus);
};

const handleVisibilityChange = (value: string) => {
  emit("update:visibility", value as EvaluationRecordFilterVisibility);
};

const handleSubmitMethodChange = (value: string) => {
  emit("update:submitMethod", value as EvaluationRecordFilterMethod);
};
</script>

<style scoped lang="scss">
.filter-grid {
  display: grid;
  grid-template-columns: minmax(220px, 1.4fr) repeat(3, minmax(160px, 0.8fr));
  gap: 0.9rem;
  min-width: 0;
}

@media (max-width: 960px) {
  .filter-grid {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 640px) {
  .filter-grid {
    grid-template-columns: 1fr;
  }
}
</style>
