<template>
  <section class="sample-outcome" :aria-label="t('evaluation.summary.sampleTitle')">
    <div class="section-head">
      <div>
        <h2>{{ t("evaluation.summary.sampleTitle") }}</h2>
        <p>{{ t("evaluation.summary.sampleDescription") }}</p>
      </div>
      <strong>{{ completionRate }}</strong>
    </div>

    <div class="sample-track" aria-hidden="true">
      <span
        v-for="segment in segments"
        :key="segment.label"
        :class="`sample-track__segment sample-track__segment--${segment.tone}`"
        :style="{ width: segment.width }"
      ></span>
    </div>

    <dl class="sample-grid">
      <div
        v-for="item in stats"
        :key="item.label"
        class="sample-stat"
        :class="`sample-stat--${item.tone}`"
      >
        <dt>{{ item.label }}</dt>
        <dd>{{ item.value }}</dd>
      </div>
    </dl>
  </section>
</template>

<script setup lang="ts">
import { useI18n } from "vue-i18n";
import type {
  EvaluationSampleSegment,
  EvaluationSampleStat,
} from "@/modules/evaluation/lib/evaluation-detail-view";

defineProps<{
  completionRate: string;
  segments: EvaluationSampleSegment[];
  stats: EvaluationSampleStat[];
}>();

const { t } = useI18n();
</script>

<style scoped lang="scss">
.sample-outcome {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  padding-top: 1.65rem;
  border-top: 1px solid rgba(148, 163, 184, 0.18);
}

.sample-outcome::before {
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

.section-head > strong {
  color: var(--color-primary);
  font-size: 1.9rem;
  font-variant-numeric: tabular-nums;
  line-height: 1;
}

.sample-track {
  display: flex;
  overflow: hidden;
  height: 0.72rem;
  background: rgba(148, 163, 184, 0.15);
}

.sample-track__segment--success {
  background: #16a34a;
}

.sample-track__segment--danger {
  background: #dc2626;
}

.sample-track__segment--warning {
  background: #f59e0b;
}

.sample-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 0;
}

.sample-stat {
  min-width: 0;
  padding: 0.75rem 0.85rem 0.75rem 0.75rem;
  border-top: 1px solid rgba(148, 163, 184, 0.13);
  border-left: 3px solid transparent;
}

.sample-stat dt {
  color: var(--color-text-subtle);
  font-size: 0.8rem;
  font-weight: 800;
}

.sample-stat dd {
  margin: 0.34rem 0 0;
  color: var(--color-text-dark);
  font-size: 1.44rem;
  font-variant-numeric: tabular-nums;
  font-weight: 800;
  line-height: 1.42;
}

.sample-stat--success {
  border-left-color: #16a34a;
}

.sample-stat--danger {
  border-left-color: #dc2626;
}

.sample-stat--warning {
  border-left-color: #f59e0b;
}

.sample-stat--primary {
  border-left-color: #2563eb;
}

.sample-stat--neutral {
  border-left-color: rgba(100, 116, 139, 0.34);
}

@media (max-width: 860px) {
  .sample-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .section-head {
    flex-direction: column;
  }
}
</style>
