import { describe, expect, it } from "vitest";
import { DEFAULT_LOCALE } from "@/app/i18n";
import { ROUTE_NAME, RouteLocation } from "@/app/router/route-names";

describe("localized route helpers", () => {
  it("injects the current locale into named route locations", () => {
    RouteLocation.setCurrentLocale("fr-FR");

    expect(RouteLocation.datasetDetail("A1_identity_leakage")).toEqual({
      name: ROUTE_NAME.DATASET_DETAIL,
      params: {
        locale: "fr-FR",
        datasetId: "A1_identity_leakage",
      },
    });

    expect(RouteLocation.agentRegister({ copyFrom: "agent_1" })).toEqual({
      name: ROUTE_NAME.AGENT_REGISTER,
      params: {
        locale: "fr-FR",
      },
      query: {
        copyFrom: "agent_1",
      },
    });
  });

  it("falls back to zh-CN when route helpers receive an unsupported locale", () => {
    RouteLocation.setCurrentLocale("de-DE");

    expect(RouteLocation.home).toEqual({
      name: ROUTE_NAME.HOME_PAGE,
      params: {
        locale: DEFAULT_LOCALE,
      },
    });
  });
});
