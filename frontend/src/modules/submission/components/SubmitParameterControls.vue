<template>
  <SectionBlock
    :title="t('submission.parameters.title')"
    :description="t('submission.parameters.description')"
  >
    <div class="field-grid">
      <div class="field field--full">
        <div class="label-row">
          <div>
            <span class="field-label">{{ t("submission.parameters.difficultyLabel") }}</span>
            <p class="field-help">
              {{ difficultyHelp }}
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
        <span class="field-label">{{ t("submission.parameters.timeoutLabel") }}</span>
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
          {{ timeoutHelp }}
        </small>
        <small v-if="timeoutWarning" class="field-warning">{{ timeoutWarning }}</small>
      </label>

      <label class="field">
        <span class="field-label">{{ t("submission.parameters.maxStepsLabel") }}</span>
        <input
          type="number"
          :value="form.parameters.maxSteps"
          :min="meta.maxSteps.min"
          :max="meta.maxSteps.max"
          :step="meta.maxSteps.step"
          class="number-input ui-input-pill ui-input-focus-ring"
          @input="handleMaxStepsInput"
          @blur="handleMaxStepsBlur"
        />
        <small class="field-help">
          {{ maxStepsHelp }}
        </small>
      </label>
    </div>
  </SectionBlock>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import SectionBlock from "@/shared/ui/page/SectionBlock.vue";
import type {
  SubmitFormState,
  SubmitMetaResponse,
} from "@/shared/types/agent-types";
import {
  getRangeSoftWarning,
  normalizeDifficulty,
  normalizeMaxSteps,
  normalizeTimeoutMinutes,
} from "@/modules/submission/model/parameter-validator";

const props = defineProps<{
  meta: SubmitMetaResponse;
}>();

const form = defineModel<SubmitFormState>({ required: true });
const { t } = useI18n();

const difficultyLabel = computed(() => form.value.parameters.difficulty.toFixed(1));
const difficultyInputValue = computed(() =>
  form.value.parameters.difficulty.toFixed(1),
);
const recommendedTimeoutMax = computed(
  () => props.meta.timeoutMinutes.recommendedMax ?? 20,
);
const difficultyHelp = computed(() =>
  t("submission.parameters.difficultyHelp", {
    min: props.meta.difficulty.min.toFixed(1),
    max: props.meta.difficulty.max.toFixed(1),
    step: props.meta.difficulty.step.toFixed(1),
  }),
);
const timeoutHelp = computed(() =>
  t("submission.parameters.timeoutHelp", {
    recommended: recommendedTimeoutMax.value,
    min: props.meta.timeoutMinutes.min,
    max: props.meta.timeoutMinutes.max,
  }),
);
const maxStepsHelp = computed(() =>
  t("submission.parameters.maxStepsHelp", {
    min: props.meta.maxSteps.min,
    max: props.meta.maxSteps.max,
  }),
);
const timeoutWarning = computed(() =>
  getRangeSoftWarning(
    form.value.parameters.timeoutMinutes,
    props.meta.timeoutMinutes,
    recommendedTimeoutMax.value,
    t,
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

const handleMaxStepsInput = (event: Event) => {
  form.value.parameters.maxSteps = normalizeMaxSteps(
    getInputValue(event),
    props.meta.maxSteps,
  );
};

const handleMaxStepsBlur = () => {
  form.value.parameters.maxSteps = normalizeMaxSteps(
    form.value.parameters.maxSteps,
    props.meta.maxSteps,
  );
};
</script>

<style scoped lang="scss">
.field-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
  min-width: 0;
}

.field {
  min-width: 0;
  padding: 1rem;
  border-radius: 0.5rem;
  border: 1px solid #e2e8f0;
  background: rgba(255, 255, 255, 0.54);
}

.field--full {
  grid-column: 1 / -1;
}

.field-label {
  display: block;
  color: #334155;
  font-weight: 600;
  overflow-wrap: anywhere;
}

.label-row {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 1rem;
  min-width: 0;
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
  overflow-wrap: anywhere;
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
  min-width: 0;
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
  min-width: 0;
  padding: 0.82rem 1rem;
}

@media (max-width: 768px) {
  .field-grid,
  .difficulty-controls {
    grid-template-columns: 1fr;
  }
}
</style>
