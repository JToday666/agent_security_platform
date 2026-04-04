<template>
  <div class="content leaderboard-page layout-page-shell layout-page-shell--wide">
    <PageHeroCard
      eyebrow="公开榜单"
      title="智能体排行榜"
      description="展示公开智能体在典型评测项上的表现，当前榜单数据由稳定 mock 数据驱动，便于后续无缝切换真实接口。"
      :chips="heroChips"
    />

    <section class="filter-card ui-surface-white">
      <div class="filter-copy">
        <h2>榜单筛选</h2>
        <p>按评测项和提交方式快速收敛到目标结果，保持榜单浏览体验简洁直观。</p>
      </div>

      <div class="filter-controls">
        <label class="filter-field">
          <span>评测项</span>
          <select v-model="selectedDataset" class="filter-select ui-input-focus-ring">
            <option value="all">全部评测项</option>
            <option v-for="dataset in datasetOptions" :key="dataset" :value="dataset">
              {{ dataset }}
            </option>
          </select>
        </label>

        <label class="filter-field">
          <span>提交方式</span>
          <select v-model="selectedMethod" class="filter-select ui-input-focus-ring">
            <option value="all">全部方式</option>
            <option value="api">API</option>
            <option value="docker">Docker</option>
          </select>
        </label>
      </div>
    </section>

    <section class="rank-table ui-surface-white">
      <div class="table-header">
        <span>排名</span>
        <span>智能体名称</span>
        <span>所属评测项</span>
        <span>提交方式</span>
        <span>得分</span>
      </div>

      <div v-for="(row, index) in filteredRows" :key="row.agentName + row.datasetName" class="table-row">
        <span class="rank-index">{{ index + 1 }}</span>
        <div class="agent-cell">
          <strong>{{ row.agentName }}</strong>
          <span>{{ row.ownerName }}</span>
        </div>
        <span>{{ row.datasetName }}</span>
        <span class="method-badge" :class="row.submitMethod">{{ row.submitMethod.toUpperCase() }}</span>
        <strong class="score">{{ row.score.toFixed(1) }}</strong>
      </div>

      <div v-if="!filteredRows.length" class="empty-state">
        当前筛选条件下暂无公开结果。
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import PageHeroCard from "@/components/common/PageHeroCard.vue";

interface LeaderboardRow {
  agentName: string;
  datasetName: string;
  ownerName: string;
  submitMethod: "api" | "docker";
  score: number;
}

const leaderboardRows: LeaderboardRow[] = [
  {
    agentName: "安全卫士 v1.0",
    datasetName: "身份信息泄露",
    ownerName: "张三",
    submitMethod: "api",
    score: 96.4,
  },
  {
    agentName: "边界巡检器",
    datasetName: "命令执行",
    ownerName: "李四",
    submitMethod: "docker",
    score: 94.7,
  },
  {
    agentName: "稳态问答引擎",
    datasetName: "本地环境破坏",
    ownerName: "王五",
    submitMethod: "api",
    score: 92.8,
  },
  {
    agentName: "合规审查助手",
    datasetName: "凭证与密钥泄露",
    ownerName: "赵六",
    submitMethod: "api",
    score: 91.3,
  },
  {
    agentName: "执行边界代理",
    datasetName: "账户或平台滥用",
    ownerName: "陈七",
    submitMethod: "docker",
    score: 89.9,
  },
  {
    agentName: "Prompt Shield Pro",
    datasetName: "表单数据篡改",
    ownerName: "周八",
    submitMethod: "api",
    score: 88.6,
  },
];

const selectedDataset = ref("all");
const selectedMethod = ref<"all" | "api" | "docker">("all");

const datasetOptions = computed(() =>
  Array.from(new Set(leaderboardRows.map((item) => item.datasetName))),
);

const filteredRows = computed(() =>
  leaderboardRows
    .filter((item) =>
      selectedDataset.value === "all" ? true : item.datasetName === selectedDataset.value,
    )
    .filter((item) =>
      selectedMethod.value === "all" ? true : item.submitMethod === selectedMethod.value,
    )
    .sort((left, right) => right.score - left.score),
);

const heroChips = computed(() => [
  {
    label: "公开结果",
    value: `${leaderboardRows.length} 条`,
  },
  {
    label: "当前显示",
    value: `${filteredRows.value.length} 条`,
  },
  {
    label: "最高分",
    value: `${filteredRows.value[0]?.score.toFixed(1) ?? "--"} 分`,
  },
]);
</script>

<style scoped>
.leaderboard-page {
  padding-bottom: 2.5rem;
}

.filter-card {
  display: grid;
  grid-template-columns: minmax(0, 0.95fr) minmax(0, 1.05fr);
  gap: 1.2rem;
  padding: 1.4rem;
  border-radius: 1.8rem;
  margin-bottom: 1.25rem;
}

.filter-copy h2 {
  margin: 0;
  color: #0f172a;
}

.filter-copy p {
  margin: 0.55rem 0 0;
  color: #64748b;
  line-height: 1.7;
}

.filter-controls {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
}

.filter-field {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
}

.filter-field span {
  color: #334155;
  font-weight: 600;
}

.filter-select {
  width: 100%;
  padding: 0.82rem 1rem;
  border: 1px solid #e2e8f0;
  border-radius: 1rem;
  background: #f8fafc;
  color: #0f172a;
}

.rank-table {
  border-radius: 1.8rem;
  overflow: hidden;
  margin-bottom: 2rem;
}

.table-header,
.table-row {
  display: grid;
  grid-template-columns: 80px 1.4fr 1.3fr 120px 100px;
  gap: 1rem;
  align-items: center;
  padding: 1.1rem 1.35rem;
}

.table-header {
  background: #f8fafc;
  font-weight: 700;
  color: #0f172a;
  border-bottom: 1px solid #e2e8f0;
}

.table-row {
  border-bottom: 1px solid #e2e8f0;
  color: #334155;
  transition: background 0.2s ease;
}

.table-row:last-of-type {
  border-bottom: none;
}

.table-row:hover {
  background: #f8fafc;
}

.rank-index {
  font-weight: 800;
  color: #2563eb;
}

.agent-cell {
  display: flex;
  flex-direction: column;
  gap: 0.22rem;
}

.agent-cell strong {
  color: #0f172a;
}

.agent-cell span {
  color: #64748b;
  font-size: 0.88rem;
}

.method-badge {
  display: inline-flex;
  width: fit-content;
  border-radius: 999px;
  padding: 0.34rem 0.72rem;
  font-size: 0.82rem;
  font-weight: 700;
}

.method-badge.api {
  background: #dbeafe;
  color: #1d4ed8;
}

.method-badge.docker {
  background: #ede9fe;
  color: #6d28d9;
}

.score {
  color: #0f172a;
}

.empty-state {
  padding: 1.4rem;
  text-align: center;
  color: #64748b;
}

@media (max-width: 960px) {
  .filter-card {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .filter-controls {
    grid-template-columns: 1fr;
  }

  .table-header,
  .table-row {
    grid-template-columns: 56px minmax(0, 1.2fr) minmax(0, 1fr);
  }

  .table-header span:nth-child(4),
  .table-header span:nth-child(5),
  .table-row > :nth-child(4),
  .table-row > :nth-child(5) {
    display: none;
  }
}
</style>
