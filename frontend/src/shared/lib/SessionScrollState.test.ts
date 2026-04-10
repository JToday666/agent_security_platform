import assert from "node:assert/strict";
import test from "node:test";

import {
  buildSessionScrollStorageKey,
  loadSessionScrollPosition,
  saveSessionScrollPosition,
} from "./SessionScrollState.ts";

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

test("buildSessionScrollStorageKey sorts params for stable keys", () => {
  assert.equal(
    buildSessionScrollStorageKey("DatasetDetail", {
      datasetId: "risk-001",
      tab: "overview",
    }),
    "agent-platform:session-scroll:v1::DatasetDetail::datasetId=risk-001&tab=overview",
  );

  assert.equal(
    buildSessionScrollStorageKey("DatasetDetail", {
      tab: "overview",
      datasetId: "risk-001",
    }),
    "agent-platform:session-scroll:v1::DatasetDetail::datasetId=risk-001&tab=overview",
  );
});

test("saveSessionScrollPosition stores normalized positive top offsets", () => {
  const storage = new MemoryStorage();
  const key = buildSessionScrollStorageKey("DatasetList");

  saveSessionScrollPosition(storage, key, -12.4);

  assert.deepEqual(loadSessionScrollPosition(storage, key), {
    left: 0,
    top: 0,
  });
});

test("loadSessionScrollPosition returns null for malformed payloads", () => {
  const storage = new MemoryStorage();
  const key = buildSessionScrollStorageKey("DatasetList");

  storage.setItem(key, "{bad json");
  assert.equal(loadSessionScrollPosition(storage, key), null);
});
