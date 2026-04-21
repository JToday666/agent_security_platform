<template>
  <div class="content records-page layout-page-shell layout-page-shell--wide">
    <PageHero
      title="评测历史"
      description="查阅任务流追踪，支持跨层级精准过滤及详情透视。"
    >
      <template #actions>
        <UiButton
          :to="RouteLocation.agentSubmit"
          variant="secondary"
          leading-icon="lucide:file-plus-2"
        >
          提交评测
        </UiButton>
      </template>
    </PageHero>

    <PageStatePanel
      v-if="loading"
      title="正在读取记录"
      message="请稍候。"
      :loading="true"
    />

    <PageStatePanel
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
        <EvaluationRecordItem
          v-for="record in filteredRecords"
          :key="record.evaluationId"
          :record="record"
        />
      </div>

      <PageStatePanel
        v-else
        title="没有匹配的任务"
        message="请调整搜索词或筛选条件。"
        tone="default"
      />
    </div>

    <PageStatePanel
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
import { RouteLocation } from "@/app/router/route-names";
import { getEvaluationRecords } from "@/modules/evaluation/api/evaluation-api";
import EvaluationFilterBar from "@/modules/evaluation/components/EvaluationFilterBar.vue";
import EvaluationRecordItem from "@/modules/evaluation/components/EvaluationRecordItem.vue";
import { filterEvaluationRecords } from "@/modules/evaluation/lib/evaluation-record-filters";
import type {
  EvaluationRecord,
  EvaluationStatus,
  SubmitMethod,
} from "@/shared/types/agent-types";
import UiButton from "@/shared/ui/actions/UiButton.vue";
import PageStatePanel from "@/shared/ui/feedback/PageStatePanel.vue";
import PageHero from "@/shared/ui/page/PageHero.vue";

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

<style scoped lang="scss">
.records-page {
  padding-bottom: 2.5rem;
}

.records-shell {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.result-bar {
  padding: 0.15rem 0 0;
  color: var(--color-text-muted);
  font-size: 0.92rem;
}

.records-list {
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
}
</style>
