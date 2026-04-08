<template>
  <SubmitSection
    title="评测参数"
    description="根据目标场景设置难度、超时时间和重试策略，提交前可再次确认。"
  >
    <div class="field-grid">
      <div class="field full">
        <div class="label-row">
          <div>
            <span>攻击难度</span>
            <p class="field-help">
              范围 {{ meta.difficulty.min.toFixed(1) }} -
              {{ meta.difficulty.max.toFixed(1) }}，步长
              {{ meta.difficulty.step.toFixed(1) }}。
            </p>
          </div>
          <strong>{{ difficultyLabel }}</strong>
        </div>

        <div class="difficulty-controls">
          <input
            type="range"
            :value="form.parameters.difficulty"
            :min="meta.difficulty.min"
            :max="meta.difficulty.max"
            :step="meta.difficulty.step"
            class="range-input"
            :style="rangeStyle"
            @input="handleDifficultyInput"
          />
          <input
            type="number"
            :value="difficultyInputValue"
            :min="meta.difficulty.min"
            :max="meta.difficulty.max"
            :step="meta.difficulty.step"
            class="number-input ui-input-pill ui-input-focus-ring"
            @input="handleDifficultyInput"
          />
        </div>
      </div>

      <label class="field">
        <span>超时时间（分钟）</span>
        <input
          type="number"
          :value="form.parameters.timeoutMinutes"
          :min="meta.timeoutMinutes.min"
          :max="meta.timeoutMinutes.max"
          :step="meta.timeoutMinutes.step"
          class="number-input ui-input-pill ui-input-focus-ring"
          @input="handleTimeoutInput"
          @blur="handleTimeoutBlur"
        />
        <small class="field-help">
          建议设置在 {{ recommendedTimeoutMax }} 分钟内；允许范围
          {{ meta.timeoutMinutes.min }} - {{ meta.timeoutMinutes.max }} 分钟。
        </small>
        <small v-if="timeoutWarning" class="field-warning">{{ timeoutWarning }}</small>
      </label>

      <label class="toggle-card">
        <div>
          <strong>失败重试</strong>
          <p>当请求或执行链路失败时，允许平台做一次自动重试。</p>
        </div>
        <input
          v-model="form.parameters.retryEnabled"
          type="checkbox"
          class="toggle-input"
        />
      </label>
    </div>
  </SubmitSection>
</template>

<script setup lang="ts">
import { computed } from "vue";
import SubmitSection from "./SubmitSection.vue";
import type { SubmitFormState, SubmitMetaResponse } from "@/types/AgentTypes";
import {
  getRangeSoftWarning,
  normalizeDifficulty,
  normalizeTimeoutMinutes,
} from "@/utils/submit";

const props = defineProps<{
  meta: SubmitMetaResponse;
}>();

const form = defineModel<SubmitFormState>({ required: true });

const difficultyLabel = computed(() => form.value.parameters.difficulty.toFixed(1));
const difficultyInputValue = computed(() =>
  form.value.parameters.difficulty.toFixed(1),
);
const recommendedTimeoutMax = computed(
  () => props.meta.timeoutMinutes.recommendedMax ?? 20,
);
const timeoutWarning = computed(() =>
  getRangeSoftWarning(
    form.value.parameters.timeoutMinutes,
    props.meta.timeoutMinutes,
    recommendedTimeoutMax.value,
  ),
);
const rangeStyle = computed(() => {
  const span = props.meta.difficulty.max - props.meta.difficulty.min;
  const progress =
    span <= 0
      ? 0
      : ((form.value.parameters.difficulty - props.meta.difficulty.min) / span) *
        100;

  return {
    "--range-progress": `${Math.min(100, Math.max(0, progress))}%`,
  };
});

const getInputValue = (event: Event): string =>
  (event.target as HTMLInputElement).value;

const handleDifficultyInput = (event: Event) => {
  form.value.parameters.difficulty = normalizeDifficulty(
    getInputValue(event),
    props.meta.difficulty,
  );
};

const handleTimeoutInput = (event: Event) => {
  form.value.parameters.timeoutMinutes = normalizeTimeoutMinutes(
    getInputValue(event),
    props.meta.timeoutMinutes,
  );
};

const handleTimeoutBlur = () => {
  form.value.parameters.timeoutMinutes = normalizeTimeoutMinutes(
    form.value.parameters.timeoutMinutes,
    props.meta.timeoutMinutes,
  );
};
</script>

<style scoped>
.field-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
  margin-top: 1rem;
}

.field,
.toggle-card {
  padding: 1rem;
  border-radius: 1.2rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}

.field.full {
  grid-column: 1 / -1;
}

.label-row {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
}

.label-row span,
.field span {
  display: block;
  color: #334155;
  font-weight: 600;
}

.label-row strong {
  color: #2563eb;
  font-size: 1.2rem;
}

.field-help,
.field-warning {
  display: block;
  margin-top: 0.42rem;
  line-height: 1.6;
}

.field-help {
  color: #64748b;
}

.field-warning {
  color: #c2410c;
  font-weight: 600;
}

.difficulty-controls {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 120px;
  gap: 1rem;
  align-items: center;
  margin-top: 0.9rem;
}

.range-input {
  appearance: none;
  width: 100%;
  height: 0.75rem;
  border-radius: 999px;
  background:
    linear-gradient(
      90deg,
      #2563eb 0%,
      #2563eb var(--range-progress, 50%),
      #dbeafe var(--range-progress, 50%),
      #dbeafe 100%
    );
  cursor: pointer;
  touch-action: pan-x;
}

.range-input::-webkit-slider-thumb {
  appearance: none;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #ffffff;
  border: 3px solid #2563eb;
  box-shadow: 0 8px 18px -10px rgba(37, 99, 235, 0.8);
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}

.range-input::-moz-range-thumb {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #ffffff;
  border: 3px solid #2563eb;
  box-shadow: 0 8px 18px -10px rgba(37, 99, 235, 0.8);
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}

.range-input:hover::-webkit-slider-thumb,
.range-input:active::-webkit-slider-thumb,
.range-input:hover::-moz-range-thumb,
.range-input:active::-moz-range-thumb {
  transform: scale(1.08);
  box-shadow: 0 10px 22px -10px rgba(37, 99, 235, 0.9);
}

.number-input {
  width: 100%;
  padding: 0.82rem 1rem;
}

.toggle-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.toggle-card strong {
  display: block;
  color: #0f172a;
}

.toggle-card p {
  margin: 0.3rem 0 0;
  color: #64748b;
  line-height: 1.6;
}

.toggle-input {
  width: 20px;
  height: 20px;
  accent-color: #2563eb;
}

@media (max-width: 768px) {
  .field-grid,
  .difficulty-controls {
    grid-template-columns: 1fr;
  }
}
</style>
