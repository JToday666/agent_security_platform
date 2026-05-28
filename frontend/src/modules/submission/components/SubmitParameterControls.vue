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
            @input="handleDifficultyRangeInput"
          />
          <input
            type="number"
            :value="difficultyDraft"
            :min="meta.difficulty.min"
            :max="meta.difficulty.max"
            :step="meta.difficulty.step"
            class="number-input ui-input-pill ui-input-focus-ring"
            @input="handleDifficultyInput"
            @blur="handleDifficultyBlur"
          />
        </div>
      </div>

      <label class="field">
        <span class="field-label">{{ t("submission.parameters.timeoutLabel") }}</span>
        <input
          type="number"
          :value="timeoutDraft"
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
          :value="maxStepsDraft"
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
import { computed, ref, watch } from "vue";
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
const recommendedTimeoutMax = computed(
  () => props.meta.timeoutMinutes.recommendedMax ?? 25,
);
const difficultyDraft = ref(form.value.parameters.difficulty.toFixed(1));
const timeoutDraft = ref(String(form.value.parameters.timeoutMinutes));
const maxStepsDraft = ref(String(form.value.parameters.maxSteps));
const editingField = ref<"difficulty" | "timeout" | "maxSteps" | null>(null);
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

watch(
  () => form.value.parameters.difficulty,
  (value) => {
    if (editingField.value !== "difficulty") {
      difficultyDraft.value = value.toFixed(1);
    }
  },
);

watch(
  () => form.value.parameters.timeoutMinutes,
  (value) => {
    if (editingField.value !== "timeout") {
      timeoutDraft.value = String(value);
    }
  },
);

watch(
  () => form.value.parameters.maxSteps,
  (value) => {
    if (editingField.value !== "maxSteps") {
      maxStepsDraft.value = String(value);
    }
  },
);

const handleDifficultyRangeInput = (event: Event) => {
  const normalized = normalizeDifficulty(
    getInputValue(event),
    props.meta.difficulty,
  );
  form.value.parameters.difficulty = normalized;
  difficultyDraft.value = normalized.toFixed(1);
};

const handleDifficultyInput = (event: Event) => {
  editingField.value = "difficulty";
  difficultyDraft.value = getInputValue(event);
};

const handleDifficultyBlur = () => {
  const normalized = normalizeDifficulty(
    difficultyDraft.value,
    props.meta.difficulty,
  );
  form.value.parameters.difficulty = normalized;
  difficultyDraft.value = normalized.toFixed(1);
  editingField.value = null;
};

const handleTimeoutInput = (event: Event) => {
  editingField.value = "timeout";
  timeoutDraft.value = getInputValue(event);
};

const handleTimeoutBlur = () => {
  const normalized = normalizeTimeoutMinutes(
    timeoutDraft.value,
    props.meta.timeoutMinutes,
  );
  form.value.parameters.timeoutMinutes = normalized;
  timeoutDraft.value = String(normalized);
  editingField.value = null;
};

const handleMaxStepsInput = (event: Event) => {
  editingField.value = "maxSteps";
  maxStepsDraft.value = getInputValue(event);
};

const handleMaxStepsBlur = () => {
  const normalized = normalizeMaxSteps(
    maxStepsDraft.value,
    props.meta.maxSteps,
  );
  form.value.parameters.maxSteps = normalized;
  maxStepsDraft.value = String(normalized);
  editingField.value = null;
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
