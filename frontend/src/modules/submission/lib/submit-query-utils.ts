const normalizeCandidateIds = (value: string | string[]): string[] => {
  const source = Array.isArray(value) ? value : [value];

  return source
    .flatMap((item) => item.split(","))
    .map((item) => item.trim())
    .filter(Boolean);
};

export const resolveEvaluationItemIdsFromQuery = (
  value: string | string[] | null | undefined,
  validEvaluationItemIds: string[],
): string[] => {
  if (!value) {
    return [];
  }

  const validIdSet = new Set(validEvaluationItemIds);
  const uniqueIds = Array.from(new Set(normalizeCandidateIds(value)));

  return uniqueIds.filter((item) => validIdSet.has(item));
};

export const buildEvaluationItemQuerySignature = (
  value: string | string[] | null | undefined,
): string => {
  if (!value) {
    return "";
  }

  return Array.isArray(value) ? value.join(",") : value;
};
