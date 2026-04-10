<template>
  <div class="content leaderboard-page layout-page-shell layout-page-shell--wide">
    <PageHeroCard
      eyebrow="公开榜单"
      title="智能体排行榜"
      description="排行榜功能仍在建设中，当前仅展示占位状态或可选 Mock 演示。"
      :chips="heroChips"
    />

    <section v-if="!showMock" class="placeholder-card ui-surface-white">
      <h2>敬请期待</h2>
      <p>
        当前版本不展示伪造业务结果。排行榜接入会在前后端接口完成后统一上线。
      </p>
    </section>

    <section v-else class="rank-list">
      <article
        v-for="(row, index) in mockRows"
        :key="row.agentName + row.datasetName"
        class="rank-item ui-surface-white"
      >
        <div class="rank-main">
          <span class="rank-index">{{ index + 1 }}</span>
          <div class="agent-cell">
            <strong>{{ row.agentName }}</strong>
            <span>{{ row.ownerName }}</span>
          </div>
          <strong class="score">{{ row.score.toFixed(1) }}</strong>
        </div>

        <div class="rank-meta">
          <div class="meta-item">
            <span class="meta-label">评测项</span>
            <span class="meta-value">{{ row.datasetName }}</span>
          </div>
          <div class="meta-item meta-item--compact">
            <span class="meta-label">提交方式</span>
            <span class="method-badge" :class="row.submitMethod">
              {{ row.submitMethod.toUpperCase() }}
            </span>
          </div>
        </div>
      </article>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { ApiConfig } from "@/shared/api/core/Config";
import PageHeroCard from "@/shared/ui/PageHeroCard.vue";

interface LeaderboardRow {
  agentName: string;
  datasetName: string;
  ownerName: string;
  submitMethod: "api" | "docker";
  score: number;
}

const showMock = ApiConfig.enableLeaderboardMock;

const mockRows: LeaderboardRow[] = [
  {
    agentName: "Guardian Mesh v2.4",
    datasetName: "身份信息泄露",
    ownerName: "张岑",
    submitMethod: "api",
    score: 94.2,
  },
  {
    agentName: "Boundary Sentinel",
    datasetName: "命令执行",
    ownerName: "周衡",
    submitMethod: "docker",
    score: 92.8,
  },
  {
    agentName: "Civic Safety Writer",
    datasetName: "虚假信息与诈骗",
    ownerName: "林澄",
    submitMethod: "api",
    score: 90.6,
  },
];

const heroChips = computed(() => [
  {
    label: "模式",
    value: showMock ? "Leaderboard Mock" : "敬请期待",
  },
  {
    label: "结果",
    value: showMock ? `${mockRows.length} 条` : "--",
  },
]);
</script>

<style scoped>
.leaderboard-page {
  padding-bottom: 2.5rem;
}

.placeholder-card {
  padding: 1.6rem;
  border-radius: 1.8rem;
  margin-bottom: 2rem;
}

.placeholder-card h2 {
  margin: 0;
  color: #0f172a;
}

.placeholder-card p {
  margin: 0.7rem 0 0;
  color: #64748b;
  line-height: 1.8;
}

.rank-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 2rem;
}

.rank-item {
  border-radius: 1.8rem;
  padding: 1.2rem 1.35rem;
}

.rank-main {
  display: grid;
  grid-template-columns: 72px minmax(0, 1fr) auto;
  align-items: center;
  gap: 1rem;
}

.rank-index {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 3rem;
  height: 3rem;
  border-radius: 999px;
  background: linear-gradient(135deg, rgba(219, 234, 254, 0.92), rgba(237, 233, 254, 0.84));
  color: #2563eb;
  font-weight: 800;
}

.agent-cell {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  min-width: 0;
}

.agent-cell strong {
  color: #0f172a;
  font-size: 1.08rem;
}

.agent-cell span {
  color: #64748b;
  font-size: 0.9rem;
}

.score {
  color: #0f172a;
  font-size: 1.25rem;
}

.rank-meta {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 1rem;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e2e8f0;
}

.meta-item {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  min-width: 0;
}

.meta-item--compact {
  align-items: flex-end;
}

.meta-label {
  color: #64748b;
  font-size: 0.84rem;
}

.meta-value {
  color: #334155;
  line-height: 1.6;
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

@media (max-width: 640px) {
  .rank-item {
    padding: 1.1rem;
    border-radius: 1.35rem;
  }

  .rank-main {
    grid-template-columns: 56px minmax(0, 1fr);
  }

  .score {
    grid-column: 1 / -1;
    padding-left: 56px;
    font-size: 1.15rem;
  }

  .rank-meta {
    grid-template-columns: 1fr;
  }

  .meta-item--compact {
    align-items: flex-start;
  }
}
</style>
