<template>
  <section class="evidence-section">
    <div class="section-head">
      <div>
        <h2>{{ t("evaluation.evidence.title") }}</h2>
        <p>{{ t("evaluation.evidence.description") }}</p>
      </div>
      <UiButton
        variant="secondary"
        leading-icon="app:action.download"
        :loading="downloadLoading"
        :disabled="!detail.finalReportAvailable || downloadLoading"
        @click="$emit('download')"
      >
        {{ t("evaluation.actions.downloadSamples") }}
      </UiButton>
    </div>

    <InlineNotice
      v-if="downloadError"
      tone="danger"
      :message="downloadError"
    />

    <div v-if="samples.length === 0" class="section-state">
      {{ t("evaluation.evidence.empty") }}
    </div>

    <div v-else class="sample-list">
      <article
        v-for="sample in samples"
        :key="sample.sampleId"
        class="sample-row"
        :class="`sample-row--${sample.normalizedResult}`"
      >
        <div class="sample-row__meta">
          <UiTag :tone="getOutcomeTone(sample.normalizedResult)" size="sm">
            {{ getOutcomeLabel(sample.normalizedResult) }}
          </UiTag>
          <div class="sample-row__copy">
            <h3>{{ sample.datasetName }}</h3>
            <p>
              {{ sample.outcomeReasonText || t("evaluation.evidence.noSummary") }}
            </p>
            <code>{{ sample.sampleId }}</code>
          </div>
        </div>
        <video
          v-if="sample.replayUrl"
          class="sample-row__video"
          :src="sample.replayUrl"
          controls
          preload="metadata"
        ></video>
        <div v-else class="sample-row__empty">
          {{ t("evaluation.evidence.noReplay") }}
        </div>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import { selectRepresentativeSamples } from "@/modules/evaluation/lib/evaluation-report-samples";
import type {
  EvaluationDetail,
  EvaluationSampleOutcome,
} from "@/shared/types/agent-types";
import UiButton from "@/shared/ui/actions/UiButton.vue";
import UiTag from "@/shared/ui/display/UiTag.vue";
import InlineNotice from "@/shared/ui/feedback/InlineNotice.vue";

const props = defineProps<{
  detail: EvaluationDetail;
  downloadLoading: boolean;
  downloadError: string;
}>();
const { t } = useI18n();

defineEmits<{
  (event: "download"): void;
}>();

const samples = computed(() =>
  selectRepresentativeSamples(props.detail.representativeSamples),
);

const getOutcomeLabel = (outcome: EvaluationSampleOutcome): string => {
  if (outcome === "failed") return t("evaluation.outcomes.failed");
  if (outcome === "error") return t("evaluation.outcomes.error");
  return t("evaluation.outcomes.success");
};

const getOutcomeTone = (
  outcome: EvaluationSampleOutcome,
): "success" | "danger" | "warning" =>
  outcome === "success" ? "success" : outcome === "failed" ? "danger" : "warning";
</script>

<style scoped lang="scss">
.evidence-section,
.sample-list {
  display: flex;
  flex-direction: column;
}

.evidence-section {
  position: relative;
  gap: 1rem;
  padding-top: 1.35rem;
  border-top: 1px solid rgba(148, 163, 184, 0.18);
}

.evidence-section::before {
  position: absolute;
  top: -1px;
  left: 0;
  width: 8rem;
  height: 1px;
  background: linear-gradient(90deg, #2563eb, rgba(37, 99, 235, 0));
  content: "";
}

.section-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.section-head h2 {
  margin: 0;
  color: var(--color-text-dark);
  font-size: 1.18rem;
}

.section-head p {
  margin: 0.35rem 0 0;
  color: var(--color-text-subtle);
  line-height: 1.68;
}

.section-state,
.sample-row__empty {
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px dashed rgba(148, 163, 184, 0.28);
  color: var(--color-text-subtle);
}

.section-state {
  min-height: 160px;
}

.sample-list {
  gap: 1rem;
}

.sample-row {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 0.9fr) minmax(280px, 1.1fr);
  gap: 1rem;
  overflow: hidden;
  padding: 1rem 1rem 1rem 0.9rem;
  border-top: 1px solid rgba(148, 163, 184, 0.16);
  background:
    radial-gradient(circle at 0% 0%, rgba(37, 99, 235, 0.06), transparent 34%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.58), rgba(248, 250, 252, 0.24));
  transition:
    background var(--duration-base) var(--ease-standard),
    transform var(--duration-base) var(--ease-standard);
}

.sample-row::before {
  position: absolute;
  inset: 0 auto 0 0;
  width: 3px;
  background: rgba(100, 116, 139, 0.36);
  content: "";
}

.sample-row:hover {
  background:
    radial-gradient(circle at 0% 0%, rgba(37, 99, 235, 0.09), transparent 34%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.72), rgba(248, 250, 252, 0.36));
  transform: translateY(-1px);
}

.sample-row--success::before {
  background: #16a34a;
}

.sample-row--failed::before {
  background: #dc2626;
}

.sample-row--error::before {
  background: #f59e0b;
}

.sample-row__meta {
  display: flex;
  align-items: flex-start;
  gap: 0.8rem;
  min-width: 0;
}

.sample-row__copy {
  min-width: 0;
}

.sample-row__copy h3 {
  margin: 0;
  color: var(--color-text-dark);
  font-size: 1rem;
}

.sample-row__copy p {
  margin: 0.5rem 0;
  color: var(--color-text-muted);
  line-height: 1.68;
}

.sample-row__copy code {
  display: block;
  overflow: hidden;
  color: var(--color-text-subtle);
  font-family: var(--font-mono, monospace);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sample-row__video,
.sample-row__empty {
  width: 100%;
  min-height: 220px;
  background: #0f172a;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.08);
}

.sample-row__video {
  aspect-ratio: 16 / 9;
}

@media (max-width: 920px) {
  .sample-row {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .section-head {
    flex-direction: column;
  }
}

@media (prefers-reduced-motion: reduce) {
  .sample-row {
    transition: none;
  }

  .sample-row:hover {
    transform: none;
  }
}
</style>
