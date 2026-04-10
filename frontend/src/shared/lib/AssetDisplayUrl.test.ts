import assert from "node:assert/strict";
import test from "node:test";

import { appendCacheBustParam } from "./AssetDisplayUrl.ts";

test("appendCacheBustParam returns empty string for blank urls", () => {
  assert.equal(appendCacheBustParam(""), "");
  assert.equal(appendCacheBustParam("   "), "");
  assert.equal(appendCacheBustParam(null), "");
});

test("appendCacheBustParam appends a version query for plain urls", () => {
  assert.equal(
    appendCacheBustParam("https://example.com/avatar.png", 123),
    "https://example.com/avatar.png?v=123",
  );
});

test("appendCacheBustParam appends a version query to urls with existing search params", () => {
  assert.equal(
    appendCacheBustParam("https://example.com/avatar.png?size=small", "abc"),
    "https://example.com/avatar.png?size=small&v=abc",
  );
});
