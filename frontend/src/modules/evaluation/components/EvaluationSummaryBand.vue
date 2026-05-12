<template>
  <section class="summary-band" :class="`summary-band--${scoreTone}`">
    <div class="score-display">
      <span>{{ t("evaluation.summary.scoreLabel") }}</span>
      <strong>{{ primaryScore }}</strong>
      <small>{{ scoreCaption }}</small>
    </div>

    <div class="summary-band__main">
      <div class="identity-line">
        <code :title="detail.evaluationId">{{ detail.evaluationId }}</code>
        <StatusTag kind="evaluation" :value="detail.status" size="sm" />
        <StatusTag kind="report" :value="reportTagValue" size="sm" />
      </div>

      <p class="status-copy">{{ detail.progress.statusText }}</p>

      <div
        class="progress-line"
        :aria-label="t('evaluation.summary.completion')"
      >
        <span :style="{ width: `${detail.progress.percent}%` }"></span>
      </div>

      <dl class="summary-grid">
        <div v-for="item in summaryItems" :key="item.label">
          <dt>{{ item.label }}</dt>
          <dd>{{ item.value }}</dd>
        </div>
      </dl>
    </div>

    <div
      v-if="hasAvailableActions(detail.controls)"
      class="summary-actions"
      :aria-label="t('evaluation.summary.taskActionsAria')"
    >
      <UiButton
        v-if="detail.controls.canPause"
        variant="secondary"
        size="sm"
        leading-icon="app:action.pause"
        :disabled="actionLoading"
        @click="$emit('open-action', 'pause')"
      >
        {{ t("evaluation.actions.pause") }}
      </UiButton>
      <UiButton
        v-if="detail.controls.canResume"
        variant="primary"
        size="sm"
        leading-icon="app:action.continue"
        :disabled="actionLoading"
        @click="$emit('run-action', 'resume')"
      >
        {{ t("evaluation.actions.continue") }}
      </UiButton>
      <UiButton
        v-if="detail.controls.canTerminate"
        variant="secondary"
        size="sm"
        leading-icon="app:action.terminate"
        :disabled="actionLoading"
        @click="$emit('open-action', 'terminate')"
      >
        {{ t("evaluation.actions.terminate") }}
      </UiButton>
      <UiButton
        v-if="detail.controls.canCancel"
        variant="danger"
        size="sm"
        leading-icon="app:action.cancel"
        :disabled="actionLoading"
        @click="$emit('open-action', 'cancel')"
      >
        {{ t("evaluation.actions.cancel") }}
      </UiButton>
    </div>
  </section>
</template>

<script setup lang="ts">
import { useI18n } from "vue-i18n";
import { hasAvailableActions } from "@/modules/evaluation/lib/evaluation-status";
import type {
  EvaluationDetailTextItem,
  EvaluationDetailTone,
  EvaluationReportTagValue,
} from "@/modules/evaluation/lib/evaluation-detail-view";
import type {
  EvaluationAction,
  EvaluationDetail,
} from "@/shared/types/agent-types";
import UiButton from "@/shared/ui/actions/UiButton.vue";
import StatusTag from "@/shared/ui/display/StatusTag.vue";

defineProps<{
  detail: EvaluationDetail;
  scoreTone: EvaluationDetailTone;
  primaryScore: string;
  scoreCaption: string;
  reportTagValue: EvaluationReportTagValue;
  summaryItems: EvaluationDetailTextItem[];
  actionLoading: boolean;
}>();

defineEmits<{
  (event: "open-action", action: EvaluationAction): void;
  (event: "run-action", action: EvaluationAction): void;
}>();

const { t } = useI18n();
</script>

<style scoped lang="scss">
.summary-band {
  position: relative;
  display: grid;
  grid-template-columns: minmax(170px, 0.28fr) minmax(0, 1fr) auto;
  gap: 1.45rem;
  align-items: stretch;
  overflow: hidden;
  padding: 1.5rem 1.2rem 1.2rem;
  border: 1px solid rgba(148, 163, 184, 0.16);
  background:
    radial-gradient(circle at 3% 10%, rgba(37, 99, 235, 0.12), transparent 32%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.78), rgba(248, 250, 252, 0.42));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.86);
}

.score-display {
  display: flex;
  min-width: 0;
  flex-direction: column;
  justify-content: center;
  padding: 0.95rem 1rem;
  border-left: 4px solid #2563eb;
  background: rgba(255, 255, 255, 0.7);
}

.score-display span,
.score-display small,
.summary-grid dt {
  color: var(--color-text-subtle);
  font-size: 0.8rem;
  font-weight: 800;
}

.score-display strong {
  margin-top: 0.2rem;
  color: var(--color-text-dark);
  font-size: 3.65rem;
  font-variant-numeric: tabular-nums;
  font-weight: 900;
  letter-spacing: 0;
  line-height: 0.95;
  white-space: nowrap;
}

.score-display small {
  margin-top: 0.55rem;
}

.summary-band--success .score-display {
  border-color: #16a34a;
}

.summary-band--warning .score-display {
  border-color: #f59e0b;
}

.summary-band--danger .score-display {
  border-color: #dc2626;
}

.summary-band__main {
  min-width: 0;
  align-self: center;
}

.identity-line {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.55rem;
  min-width: 0;
}

.identity-line code {
  max-width: min(42vw, 520px);
  overflow: hidden;
  color: var(--color-text-dark);
  font-family: var(--font-mono, monospace);
  font-weight: 800;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.status-copy {
  margin: 0.75rem 0 0;
  color: var(--color-text-muted);
  line-height: 1.68;
}

.progress-line {
  overflow: hidden;
  height: 0.42rem;
  margin-top: 0.85rem;
  background: rgba(148, 163, 184, 0.16);
}

.progress-line span {
  display: block;
  height: 100%;
  background: var(--grad-progress);
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0;
  margin: 1rem 0 0;
}

.summary-grid div {
  min-width: 0;
  padding: 0.75rem 0.85rem 0.75rem 0;
  border-top: 1px solid rgba(148, 163, 184, 0.13);
}

.summary-grid dd {
  margin: 0.34rem 0 0;
  color: var(--color-text-dark);
  font-weight: 800;
  line-height: 1.42;
}

.summary-actions {
  display: flex;
  flex-wrap: wrap;
  align-content: flex-start;
  justify-content: flex-end;
  gap: 0.55rem;
}

@media (max-width: 1180px) {
  .summary-band {
    grid-template-columns: minmax(150px, 0.3fr) minmax(0, 1fr);
  }

  .summary-actions {
    grid-column: 1 / -1;
    justify-content: flex-start;
  }
}

@media (max-width: 860px) {
  .summary-band,
  .summary-grid {
    grid-template-columns: 1fr;
  }

  .identity-line code {
    max-width: 100%;
  }

  .summary-actions :deep(.ui-button) {
    width: 100%;
  }
}

@media (max-width: 640px) {
  .summary-band {
    padding-inline: 0.85rem;
  }

  .score-display strong {
    font-size: 2.65rem;
  }
}
</style>
