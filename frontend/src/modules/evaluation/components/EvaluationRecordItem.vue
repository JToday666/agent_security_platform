<template>
  <article class="evaluation-record-item">
    <div class="evaluation-record-item__main">
      <div class="evaluation-record-item__copy">
        <div class="evaluation-record-item__head">
          <h3>{{ record.agentName }}</h3>
          <div class="evaluation-record-item__tags">
            <StatusTag kind="evaluation" :value="record.status" size="sm" />
            <StatusTag
              kind="leaderboard"
              :value="leaderboardStatus"
              size="sm"
            />
            <StatusTag kind="method" :value="record.submitMethod" size="sm" />
          </div>
        </div>

        <p class="evaluation-record-item__datasets">
          {{
            t("evaluation.records.datasetPrefix", {
              datasets: record.datasetNames.join(
                t("evaluation.common.listSeparator"),
              ),
            })
          }}
        </p>

        <p class="evaluation-record-item__meta">
          {{ t("evaluation.records.createdAt", { time: createdAt }) }}
          <span v-if="finalizationReason"> · {{ finalizationReason }}</span>
        </p>

        <div class="evaluation-record-item__progress">
          <div class="evaluation-record-item__progress-bar">
            <div
              class="evaluation-record-item__progress-fill"
              :style="{ width: `${record.progressPercent}%` }"
            ></div>
          </div>
          <span class="evaluation-record-item__progress-text">
            {{ record.progressPercent }}%
          </span>
        </div>
      </div>

      <div class="evaluation-record-item__actions">
        <Button :to="detailTo" variant="primary">
          {{ t("evaluation.actions.viewDetails") }}
        </Button>
      </div>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import type { EvaluationRecord } from "@/shared/types/agent-types";
import { RouteLocation } from "@/app/router/route-names";
import Button from "@/shared/ui/actions/UiButton.vue";
import StatusTag from "@/shared/ui/display/StatusTag.vue";
import { formatDateTimeLabel } from "@/modules/attack-scenario-library/lib/attack-scenario-library-utils";
import { getFinalizationReasonLabel } from "@/modules/evaluation/lib/evaluation-status";
import { getEvaluationLeaderboardStatus } from "@/modules/evaluation/lib/evaluation-record-filters";

const props = defineProps<{
  record: EvaluationRecord;
}>();
const { t } = useI18n();

const detailTo = computed(() =>
  RouteLocation.evaluationDetail(props.record.evaluationId),
);

const createdAt = computed(() => formatDateTimeLabel(props.record.createdAt));
const leaderboardStatus = computed(() =>
  getEvaluationLeaderboardStatus(props.record),
);
const finalizationReason = computed(() =>
  getFinalizationReasonLabel(props.record.finalizationReason, t),
);
</script>

<style scoped lang="scss">
.evaluation-record-item {
  position: relative;
  padding: 1.15rem 0.85rem 0.95rem;
  border-top: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: var(--radius-control-sm);
  transition:
    border-color var(--duration-fast) var(--ease-standard),
    background var(--duration-fast) var(--ease-standard),
    box-shadow var(--duration-fast) var(--ease-standard),
    transform var(--duration-fast) var(--ease-standard);
}

.evaluation-record-item::before {
  position: absolute;
  inset: 0 auto 0 0;
  width: 3px;
  content: "";
  border-radius: var(--radius-pill);
  background: var(--grad-primary);
  opacity: 0;
  transform: scaleY(0.55);
  transform-origin: center;
  transition:
    opacity var(--duration-fast) var(--ease-standard),
    transform var(--duration-fast) var(--ease-standard);
}

.evaluation-record-item:hover,
.evaluation-record-item:focus-within {
  border-color: var(--color-border-strong);
  background:
    radial-gradient(circle at 0 0, rgba(99, 102, 241, 0.09), transparent 28%),
    rgba(255, 255, 255, 0.52);
  box-shadow: var(--shadow-surface-soft);
  transform: translateY(-1px);
}

.evaluation-record-item:hover::before,
.evaluation-record-item:focus-within::before {
  opacity: 1;
  transform: scaleY(1);
}

.evaluation-record-item__main {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.evaluation-record-item__copy {
  flex: 1;
  min-width: 0;
  padding-left: 0.35rem;
}

.evaluation-record-item__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.evaluation-record-item__head h3 {
  margin: 0;
  color: var(--color-text-dark);
  font-size: 1.08rem;
}

.evaluation-record-item__tags {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 0.45rem;
}

.evaluation-record-item__datasets,
.evaluation-record-item__meta {
  margin: 0.6rem 0 0;
  color: var(--color-text-muted);
  line-height: 1.68;
}

.evaluation-record-item__progress {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-top: 0.92rem;
}

.evaluation-record-item__progress-bar {
  flex: 1;
  height: 8px;
  border-radius: 999px;
  overflow: hidden;
  background: rgba(226, 232, 240, 0.96);
}

.evaluation-record-item__progress-fill {
  height: 100%;
  background: var(--grad-progress);
}

.evaluation-record-item__progress-text {
  min-width: 46px;
  color: var(--color-text-main);
  font-weight: 700;
  text-align: right;
}

.evaluation-record-item__actions {
  flex-shrink: 0;
}

@media (max-width: 768px) {
  .evaluation-record-item__main,
  .evaluation-record-item__head {
    flex-direction: column;
  }

  .evaluation-record-item__tags {
    justify-content: flex-start;
  }

  .evaluation-record-item__actions {
    width: 100%;
  }
}

@media (prefers-reduced-motion: reduce) {
  .evaluation-record-item,
  .evaluation-record-item::before {
    transition: none;
  }

  .evaluation-record-item:hover,
  .evaluation-record-item:focus-within {
    transform: none;
  }
}
</style>
