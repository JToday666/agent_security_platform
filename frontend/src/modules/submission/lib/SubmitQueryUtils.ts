const normalizeCandidateIds = (value: string | string[]): string[] => {
  const source = Array.isArray(value) ? value : [value];

  return source
    .flatMap((item) => item.split(","))
    .map((item) => item.trim())
    .filter(Boolean);
};

export const resolveDatasetIdsFromQuery = (
  value: string | string[] | null | undefined,
  validDatasetIds: string[],
): string[] => {
  if (!value) {
    return [];
  }

  const validIdSet = new Set(validDatasetIds);
  const uniqueIds = Array.from(new Set(normalizeCandidateIds(value)));

  return uniqueIds.filter((item) => validIdSet.has(item));
};
