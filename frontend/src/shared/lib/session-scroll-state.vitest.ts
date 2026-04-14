import { describe, expect, it } from "vitest";
import {
  buildSessionScrollStorageKey,
  loadSessionScrollPosition,
  saveSessionScrollPosition,
} from "./session-scroll-state";
import { STORAGE_KEYS } from "@/shared/constants/storage-keys";

class MemoryStorage {
  private readonly store = new Map<string, string>();

  getItem(key: string): string | null {
    return this.store.get(key) ?? null;
  }

  setItem(key: string, value: string): void {
    this.store.set(key, value);
  }

  removeItem(key: string): void {
    this.store.delete(key);
  }
}

describe("SessionScrollState", () => {
  it("sorts params for stable keys", () => {
    expect(
      buildSessionScrollStorageKey("DatasetDetail", {
        datasetId: "risk-001",
        tab: "overview",
      }),
    ).toBe(
      `${STORAGE_KEYS.session.scroll}::DatasetDetail::datasetId=risk-001&tab=overview`,
    );

    expect(
      buildSessionScrollStorageKey("DatasetDetail", {
        tab: "overview",
        datasetId: "risk-001",
      }),
    ).toBe(
      `${STORAGE_KEYS.session.scroll}::DatasetDetail::datasetId=risk-001&tab=overview`,
    );
  });

  it("stores normalized positive top offsets", () => {
    const storage = new MemoryStorage();
    const key = buildSessionScrollStorageKey("DatasetList");

    saveSessionScrollPosition(storage, key, -12.4);

    expect(loadSessionScrollPosition(storage, key)).toEqual({
      left: 0,
      top: 0,
    });
  });

  it("returns null for malformed payloads", () => {
    const storage = new MemoryStorage();
    const key = buildSessionScrollStorageKey("DatasetList");

    storage.setItem(key, "{bad json");
    expect(loadSessionScrollPosition(storage, key)).toBeNull();
  });
});
