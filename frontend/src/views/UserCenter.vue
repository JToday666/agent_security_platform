<template>
  <div class="content records-card layout-page-panel layout-page-panel--lg ui-surface-glass">
    <h1 class="page-title layout-page-title">评测记录</h1>
    <p class="page-subtitle layout-page-subtitle">
      已提交任务会优先展示最近创建的记录，新的 mock 提交会直接出现在这里。
    </p>

    <div v-if="loading" class="state-card layout-state-card ui-surface-white">
      <h2>正在读取记录</h2>
      <p>系统正在同步您最近的评测任务与执行状态。</p>
    </div>

    <div v-else-if="error" class="state-card layout-state-card ui-surface-white">
      <h2>记录加载失败</h2>
      <p>{{ error }}</p>
      <button class="retry-btn layout-retry-btn ui-btn ui-btn-pill ui-btn-gradient" @click="loadRecords">
        重试
      </button>
    </div>

    <div v-else-if="records.length" class="records-list">
      <article
        v-for="record in records"
        :key="record.evaluationId"
        class="record-item ui-surface-white"
      >
        <div class="record-info">
          <div class="title-row">
            <h3>{{ record.agentName }}</h3>
            <span class="status-badge" :class="record.status">{{ statusLabels[record.status] }}</span>
            <span class="visibility-badge" :class="{ public: record.publicToLeaderboard }">
              {{ record.publicToLeaderboard ? "公开" : "私有" }}
            </span>
          </div>

          <p class="record-meta">
            评测项：{{ record.datasetNames.join("、") }}
          </p>
          <p class="record-meta">
            创建时间：{{ formatDateTimeLabel(record.createdAt) }} · 提交方式：{{ record.submitMethod.toUpperCase() }}
          </p>
        </div>

        <div class="record-side">
          <strong class="score">{{ record.score ? `${record.score} 分` : "待生成" }}</strong>
          <router-link
            :to="RouteLocation.evaluationDetail(record.evaluationId)"
            class="view-btn ui-btn ui-btn-pill ui-btn-gradient ui-btn-hover-lift"
          >
            查看详情
          </router-link>
        </div>
      </article>
    </div>

    <div v-else class="empty-state layout-state-card">
      <p>您还没有提交过智能体评测。</p>
      <router-link
        :to="RouteLocation.agentSubmit"
        class="btn layout-retry-btn ui-btn ui-btn-pill ui-btn-gradient ui-btn-hover-lift"
      >
        立即提交
      </router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { getEvaluationRecords } from "@/api/AgentService";
import { RouteLocation } from "@/router/RouteNames";
import type { EvaluationRecord } from "@/types/AgentTypes";
import { formatDateTimeLabel } from "@/utils/DatasetUtils";

const records = ref<EvaluationRecord[]>([]);
const loading = ref(true);
const error = ref("");

const statusLabels = {
  pending: "排队中",
  running: "执行中",
  completed: "已完成",
};

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
.records-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.record-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 1.25rem 1.4rem;
  border-radius: 1.3rem;
  transition: transform 0.2s ease;
}

.record-item:hover {
  transform: translateX(4px);
}

.record-info {
  flex: 1;
}

.title-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
  align-items: center;
}

.title-row h3 {
  margin: 0;
  font-size: 1.25rem;
  color: #0f172a;
}

.status-badge,
.visibility-badge {
  border-radius: 999px;
  padding: 0.28rem 0.72rem;
  font-size: 0.82rem;
  font-weight: 700;
}

.status-badge.pending {
  background: #ffedd5;
  color: #c2410c;
}

.status-badge.running {
  background: #dbeafe;
  color: #1d4ed8;
}

.status-badge.completed {
  background: #dcfce7;
  color: #15803d;
}

.visibility-badge {
  background: #e2e8f0;
  color: #475569;
}

.visibility-badge.public {
  background: #ede9fe;
  color: #6d28d9;
}

.record-meta {
  margin: 0.55rem 0 0;
  color: #64748b;
  line-height: 1.7;
}

.record-side {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.8rem;
}

.score {
  color: #0f172a;
  font-size: 1.1rem;
}

.view-btn {
  padding: 0.74rem 1.05rem;
  text-decoration: none;
}

.empty-state {
  text-align: center;
}

.empty-state p {
  margin: 0.8rem auto 0;
  max-width: 520px;
  color: #64748b;
  line-height: 1.7;
}

.btn {
  text-decoration: none;
}

@media (max-width: 768px) {
  .record-item {
    flex-direction: column;
    align-items: stretch;
  }

  .record-side {
    align-items: stretch;
  }
}
</style>
