import type {
  EvaluationRepresentativeSample,
  EvaluationRepresentativeSamples,
} from "@/shared/types/agent-types";

export const selectRepresentativeSamples = (
  samples: EvaluationRepresentativeSamples,
): EvaluationRepresentativeSample[] => {
  const selected: EvaluationRepresentativeSample[] = [];
  if (samples.success) {
    selected.push(samples.success);
  }

  const riskSample = samples.failed ?? samples.error;
  if (riskSample) {
    selected.push(riskSample);
  }

  if (selected.length === 0 && samples.error) {
    selected.push(samples.error);
  }

  return selected.slice(0, 2);
};
