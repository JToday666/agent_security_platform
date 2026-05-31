import { describe, expect, it } from "vitest";
import { resolveHomeSectionScrollTop } from "@/modules/public/model/home-page-scroll";

describe("resolveHomeSectionScrollTop", () => {
  it("places the target section in an upper-middle reading position", () => {
    const scrollTop = resolveHomeSectionScrollTop({
      currentScrollY: 400,
      targetTop: 900,
      viewportHeight: 1000,
      documentHeight: 4000,
      navHeight: 72,
    });

    expect(scrollTop).toBe(996);
  });

  it("clamps the target position near the bottom of the page", () => {
    const scrollTop = resolveHomeSectionScrollTop({
      currentScrollY: 2500,
      targetTop: 900,
      viewportHeight: 1000,
      documentHeight: 3200,
      navHeight: 72,
    });

    expect(scrollTop).toBe(2200);
  });
});
