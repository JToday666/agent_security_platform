<template>
  <div class="content records-page layout-page-shell layout-page-shell--wide">
    <PageHeroCard
      title="评测记录"
      description="查看任务状态、筛选记录并进入详情页。"
      :chips="heroChips"
      tone="workspace"
      title-tone="brand"
    >
      <template #actions>
        <UiButton :to="RouteLocation.agentSubmit" variant="secondary">
          提交评测
        </UiButton>
      </template>
    </PageHeroCard>

    <PageStateCard
      v-if="loading"
      title="正在读取记录"
      message="请稍候。"
      :loading="true"
    />

    <PageStateCard
      v-else-if="error"
      title="记录加载失败"
      :message="error"
      action-text="重试"
      @action="loadRecords"
    />

    <div v-else-if="records.length" class="records-shell">
      <EvaluationFilterBar
        :search="search"
        :status="status"
        :visibility="visibility"
        :submit-method="submitMethod"
        @update:search="search = $event"
        @update:status="status = $event"
        @update:visibility="visibility = $event"
        @update:submitMethod="submitMethod = $event"
      />

      <div class="result-bar">
        <span>显示 {{ filteredRecords.length }} / {{ records.length }} 条任务</span>
      </div>

      <div v-if="filteredRecords.length" class="records-list">
        <EvaluationRecordCard
          v-for="record in filteredRecords"
          :key="record.evaluationId"
          :record="record"
        />
      </div>

      <PageStateCard
        v-else
        title="没有匹配的任务"
        message="请调整搜索词或筛选条件。"
        tone="default"
      />
    </div>

    <PageStateCard
      v-else
      title="还没有评测记录"
      message="创建第一条评测任务后，这里会显示进度和结果。"
      action-text="立即提交"
      @action="$router.push(RouteLocation.agentSubmit)"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { RouteLocation } from "@/app/router/RouteNames";
import { getEvaluationRecords } from "@/modules/evaluation/api";
import EvaluationFilterBar from "@/modules/evaluation/components/EvaluationFilterBar.vue";
import EvaluationRecordCard from "@/modules/evaluation/components/EvaluationRecordCard.vue";
import { filterEvaluationRecords } from "@/modules/evaluation/lib";
import type {
  EvaluationRecord,
  EvaluationStatus,
  SubmitMethod,
} from "@/shared/types/AgentTypes";
import PageHeroCard from "@/shared/ui/page/PageHeroCard.vue";
import PageStateCard from "@/shared/ui/feedback/PageStateCard.vue";
import UiButton from "@/shared/ui/actions/UiButton.vue";

const $router = useRouter();
const records = ref<EvaluationRecord[]>([]);
const loading = ref(true);
const error = ref("");

const search = ref("");
const status = ref<"all" | EvaluationStatus>("all");
const visibility = ref<"all" | "public" | "private">("all");
const submitMethod = ref<"all" | SubmitMethod>("all");

const filteredRecords = computed(() =>
  filterEvaluationRecords(records.value, {
    status: status.value,
    visibility: visibility.value,
    submitMethod: submitMethod.value,
    search: search.value,
  }),
);

const heroChips = computed(() => [
  { label: "任务总数", value: String(records.value.length) },
  {
    label: "运行中",
    value: String(
      records.value.filter((item) => item.status === "running").length,
    ),
  },
  {
    label: "已完成",
    value: String(
      records.value.filter((item) => item.status === "completed").length,
    ),
  },
]);

const loadRecords = async () => {
  loading.value = true;
  error.value = "";

  try {
    records.value = await getEvaluationRecords();
  } catch (loadError) {
    error.value =
      loadError instanceof Error ? loadError.message : "评测记录加载失败。";
  } finally {
    loading.value = false;
  }
};

onMounted(async () => {
  await loadRecords();
});
</script>

<style scoped>
.records-page {
  padding-bottom: 2.5rem;
}

.records-shell {
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
}

.result-bar {
  color: var(--color-text-muted);
  font-size: 0.92rem;
}

.records-list {
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
}
</style>