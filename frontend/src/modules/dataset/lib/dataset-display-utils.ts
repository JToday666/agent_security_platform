import { REFERENCE_DATASET_TAXONOMY } from "@/modules/dataset/model/dataset-taxonomy";
import { normalizeDatasetId } from "@/modules/dataset/model/dataset-id-aliases";
import { translateRuntimeMessage } from "@/app/i18n/runtime-translator";

const INTERNAL_DATASET_CODE_PATTERN = /^[A-Z][A-Z0-9_-]*\d+$/;

const PUBLIC_DATASET_NAME_MAP = new Map(
  REFERENCE_DATASET_TAXONOMY.flatMap((category) =>
    category.datasets.flatMap((dataset) => [
      [dataset.datasetId, dataset.name] as const,
      [normalizeDatasetId(dataset.datasetId), dataset.name] as const,
    ]),
  ),
);

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
  const normalizedDatasetId = normalizeDatasetId(datasetId);
  const normalizedPreferredName = normalizeLabel(preferredName);
  if (
    normalizedPreferredName &&
    !isInternalDatasetCodeLike(normalizedPreferredName, normalizedDatasetId)
  ) {
    return normalizedPreferredName;
  }

  const taxonomyName = PUBLIC_DATASET_NAME_MAP.get(
    normalizeLabel(normalizedDatasetId),
  );
  if (taxonomyName) {
    return taxonomyName;
  }

  return translateRuntimeMessage("dataset.fallback.dataset");
};

export const resolvePublicDatasetNames = (
  datasetIds: string[],
  preferredNames: readonly (string | null | undefined)[] = [],
): string[] =>
  datasetIds.map((datasetId, index) =>
    resolvePublicDatasetName(datasetId, preferredNames[index]),
  );
