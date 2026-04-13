<template>
  <SectionCard title="筛选记录" description="按关键词、状态、可见性和提交方式筛选记录。">
    <div class="filter-grid">
      <FormField
        label="搜索"
        :model-value="search"
        type="search"
        placeholder="按智能体名称或数据集搜索"
        leading-icon="lucide:search"
        @update:model-value="$emit('update:search', $event)"
      />

      <FormField
        label="状态"
        :model-value="status"
        type="select"
        :options="statusOptions"
        @update:model-value="handleStatusChange"
      />

      <FormField
        label="可见性"
        :model-value="visibility"
        type="select"
        :options="visibilityOptions"
        @update:model-value="handleVisibilityChange"
      />

      <FormField
        label="提交方式"
        :model-value="submitMethod"
        type="select"
        :options="methodOptions"
        @update:model-value="handleSubmitMethodChange"
      />
    </div>
  </SectionCard>
</template>

<script setup lang="ts">
import type {
  EvaluationRecordFilterMethod,
  EvaluationRecordFilterStatus,
  EvaluationRecordFilterVisibility,
} from "@/modules/evaluation/lib";
import FormField from "@/shared/ui/forms/FormField.vue";
import SectionCard from "@/shared/ui/page/SectionCard.vue";

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

const statusOptions: Array<{ label: string; value: EvaluationRecordFilterStatus }> = [
  { label: "全部状态", value: "all" },
  { label: "排队中", value: "pending" },
  { label: "执行中", value: "running" },
  { label: "已暂停", value: "paused" },
  { label: "已完成", value: "completed" },
  { label: "已失败", value: "failed" },
  { label: "已取消", value: "canceled" },
  { label: "已终止", value: "terminated" },
];

const visibilityOptions: Array<{ label: string; value: EvaluationRecordFilterVisibility }> = [
  { label: "全部可见性", value: "all" },
  { label: "公开", value: "public" },
  { label: "私有", value: "private" },
];

const methodOptions: Array<{ label: string; value: EvaluationRecordFilterMethod }> = [
  { label: "全部方式", value: "all" },
  { label: "API", value: "api" },
  { label: "Docker", value: "docker" },
];

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

<style scoped>
.filter-grid {
  display: grid;
  grid-template-columns: minmax(220px, 1.4fr) repeat(3, minmax(140px, 0.8fr));
  gap: 0.85rem;
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