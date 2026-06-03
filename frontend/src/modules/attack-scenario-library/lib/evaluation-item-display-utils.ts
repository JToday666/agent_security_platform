import { translateRuntimeMessage } from "@/app/i18n/runtime-translator";

const INTERNAL_DATASET_CODE_PATTERN = /^[A-G]\d(?:_[a-z0-9]+)+$/i;

const normalizeLabel = (value?: string | null): string => value?.trim() ?? "";

const isInternalDatasetCodeLike = (
  value: string,
  datasetId: string,
): boolean => {
  const normalizedValue = normalizeLabel(value);
  const normalizedDatasetId = normalizeLabel(datasetId);

  if (!normalizedValue) {
    return false;
  }

  return (
    normalizedValue.localeCompare(normalizedDatasetId, undefined, {
      sensitivity: "accent",
    }) === 0 || INTERNAL_DATASET_CODE_PATTERN.test(normalizedValue)
  );
};

export const resolvePublicDatasetName = (
  datasetId: string,
  preferredName?: string | null,
): string => {
  const normalizedDatasetId = normalizeLabel(datasetId);
  const normalizedPreferredName = normalizeLabel(preferredName);
  if (
    normalizedPreferredName &&
    !isInternalDatasetCodeLike(normalizedPreferredName, normalizedDatasetId)
  ) {
    return normalizedPreferredName;
  }

  return translateRuntimeMessage(
    "attackScenarioLibrary.fallback.unnamedEvaluationItem",
  );
};

export const resolvePublicDatasetNames = (
  datasetIds: string[],
  preferredNames: readonly (string | null | undefined)[] = [],
): string[] =>
  datasetIds.map((datasetId, index) =>
    resolvePublicDatasetName(datasetId, preferredNames[index]),
  );
