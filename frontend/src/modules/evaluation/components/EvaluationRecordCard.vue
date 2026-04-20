<template>
  <article class="record-card ui-surface-white ui-hover-card">
    <div class="record-main">
      <div class="record-copy">
        <div class="record-head">
          <h3>{{ record.agentName }}</h3>
          <div class="record-tags">
            <StatusTag kind="evaluation" :value="record.status" size="sm" />
            <StatusTag kind="visibility" :value="record.publicToLeaderboard" size="sm" />
            <StatusTag kind="method" :value="record.submitMethod" size="sm" />
          </div>
        </div>

        <p class="record-datasets">
          数据集：{{ record.datasetNames.join("、") }}
        </p>

        <p class="record-meta">
          创建于 {{ createdAt }}
          <span v-if="finalizationReason"> · {{ finalizationReason }}</span>
        </p>

        <div class="progress-row">
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: `${record.progressPercent}%` }"></div>
          </div>
          <span class="progress-text">{{ record.progressPercent }}%</span>
        </div>
      </div>

      <div class="record-actions">
        <Button :to="detailTo" variant="primary">
          查看详情
        </Button>
      </div>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { EvaluationRecord } from "@/shared/types/agent-types";
import { RouteLocation } from "@/app/router/route-names";
import Button from "@/shared/ui/actions/UiButton.vue";
import StatusTag from "@/shared/ui/display/StatusTag.vue";
import { formatDateTimeLabel } from "@/modules/dataset/lib/dataset-utils";
import { getFinalizationReasonLabel } from "@/modules/evaluation/lib/evaluation-status";

const props = defineProps<{
  record: EvaluationRecord;
}>();

const detailTo = computed(() =>
  RouteLocation.evaluationDetail(props.record.evaluationId),
);

const createdAt = computed(() => formatDateTimeLabel(props.record.createdAt));
const finalizationReason = computed(() =>
  getFinalizationReasonLabel(props.record.finalizationReason),
);
</script>

<style scoped lang="scss">
.record-card {
  border-radius: 1.35rem;
  padding: 1.05rem 1.12rem;
}

.record-main {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.record-copy {
  flex: 1;
  min-width: 0;
}

.record-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.record-head h3 {
  margin: 0;
  color: var(--color-text-dark);
  font-size: 1.12rem;
}

.record-tags {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 0.45rem;
}

.record-datasets,
.record-meta {
  margin: 0.62rem 0 0;
  color: var(--color-text-muted);
  line-height: 1.7;
}

.progress-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-top: 0.92rem;
}

.progress-bar {
  flex: 1;
  height: 8px;
  border-radius: 999px;
  overflow: hidden;
  background: rgba(226, 232, 240, 0.96);
}

.progress-fill {
  height: 100%;
  background: var(--grad-progress);
}

.progress-text {
  min-width: 46px;
  color: var(--color-text-main);
  font-weight: 700;
  text-align: right;
}

.record-actions {
  flex-shrink: 0;
}

@media (max-width: 768px) {
  .record-main,
  .record-head {
    flex-direction: column;
  }

  .record-tags {
    justify-content: flex-start;
  }

  .record-actions {
    width: 100%;
  }
}
</style>
