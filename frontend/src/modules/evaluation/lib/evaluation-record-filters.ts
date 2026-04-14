import type {
  EvaluationRecord,
  EvaluationStatus,
  SubmitMethod,
} from "@/shared/types/agent-types";

export type EvaluationRecordFilterStatus = "all" | EvaluationStatus;
export type EvaluationRecordFilterVisibility = "all" | "public" | "private";
export type EvaluationRecordFilterMethod = "all" | SubmitMethod;

export interface EvaluationRecordFilters {
  status: EvaluationRecordFilterStatus;
  visibility: EvaluationRecordFilterVisibility;
  submitMethod: EvaluationRecordFilterMethod;
  search: string;
}

const normalizeSearch = (value: string): string => value.trim().toLowerCase();

export const filterEvaluationRecords = (
  records: EvaluationRecord[],
  filters: EvaluationRecordFilters,
): EvaluationRecord[] => {
  const normalizedSearch = normalizeSearch(filters.search);

  return records.filter((record) => {
    if (filters.status !== "all" && record.status !== filters.status) {
      return false;
    }

    if (filters.visibility === "public" && !record.publicToLeaderboard) {
      return false;
    }

    if (filters.visibility === "private" && record.publicToLeaderboard) {
      return false;
    }

    if (
      filters.submitMethod !== "all" &&
      record.submitMethod !== filters.submitMethod
    ) {
      return false;
    }

    if (!normalizedSearch) {
      return true;
    }

    const haystacks = [record.agentName, ...record.datasetNames].map((item) =>
      item.toLowerCase(),
    );

    return haystacks.some((item) => item.includes(normalizedSearch));
  });
};
