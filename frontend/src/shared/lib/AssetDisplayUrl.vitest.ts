import { describe, expect, it } from "vitest";
import { appendCacheBustParam } from "./AssetDisplayUrl";

describe("appendCacheBustParam", () => {
  it("returns empty string for blank urls", () => {
    expect(appendCacheBustParam("")).toBe("");
    expect(appendCacheBustParam("   ")).toBe("");
    expect(appendCacheBustParam(null)).toBe("");
  });

  it("appends a version query for plain urls", () => {
    expect(appendCacheBustParam("https://example.com/avatar.png", 123)).toBe(
      "https://example.com/avatar.png?v=123",
    );
  });

  it("appends a version query to urls with existing search params", () => {
    expect(
      appendCacheBustParam("https://example.com/avatar.png?size=small", "abc"),
    ).toBe("https://example.com/avatar.png?size=small&v=abc");
  });
});
