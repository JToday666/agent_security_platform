import { describe, expect, it } from "vitest";
import { resolveDatasetIdsFromQuery } from "./SubmitQueryUtils";

describe("resolveDatasetIdsFromQuery", () => {
  it("keeps known ids and removes duplicates", () => {
    const result = resolveDatasetIdsFromQuery(
      "A1_identity,A1_identity,B1_prompt",
      ["A1_identity", "B1_prompt", "C1_other"],
    );

    expect(result).toEqual(["A1_identity", "B1_prompt"]);
  });

  it("accepts array query values", () => {
    const result = resolveDatasetIdsFromQuery(
      ["A1_identity,B1_prompt", "C1_other"],
      ["A1_identity", "B1_prompt", "C1_other"],
    );

    expect(result).toEqual(["A1_identity", "B1_prompt", "C1_other"]);
  });

  it("returns empty array for unknown ids", () => {
    const result = resolveDatasetIdsFromQuery("Z1_unknown", [
      "A1_identity",
      "B1_prompt",
    ]);

    expect(result).toEqual([]);
  });
});
