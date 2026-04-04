import { REFERENCE_DATASET_TAXONOMY } from "@/constants/DatasetTaxonomy";

const INTERNAL_DATASET_CODE_PATTERN = /^[A-Z][A-Z0-9_-]*\d+$/;
const GENERIC_DATASET_LABEL = "数据集";

const PUBLIC_DATASET_NAME_MAP = new Map(
  REFERENCE_DATASET_TAXONOMY.flatMap((category) =>
    category.datasets.map(
      (dataset) => [dataset.datasetId, dataset.name] as const,
    ),
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
  const normalizedPreferredName = normalizeLabel(preferredName);
  if (
    normalizedPreferredName &&
    !isInternalDatasetCodeLike(normalizedPreferredName, datasetId)
  ) {
    return normalizedPreferredName;
  }

  const taxonomyName = PUBLIC_DATASET_NAME_MAP.get(normalizeLabel(datasetId));
  if (taxonomyName) {
    return taxonomyName;
  }

  return GENERIC_DATASET_LABEL;
};

export const resolvePublicDatasetNames = (
  datasetIds: string[],
  preferredNames: readonly (string | null | undefined)[] = [],
): string[] =>
  datasetIds.map((datasetId, index) =>
    resolvePublicDatasetName(datasetId, preferredNames[index]),
  );
