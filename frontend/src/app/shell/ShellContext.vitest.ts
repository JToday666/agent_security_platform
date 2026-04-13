import { describe, expect, it } from "vitest";
import { ROUTE_NAME } from "../router/RouteNames";
import { isWorkspaceRouteName, resolveShellContext } from "./ShellContext";

describe("ShellContext", () => {
  it("returns public for showcase routes and unknown routes", () => {
    expect(resolveShellContext(ROUTE_NAME.HOME_PAGE)).toBe("public");
    expect(resolveShellContext(ROUTE_NAME.DATASET_LIST)).toBe("public");
    expect(resolveShellContext("UnknownRoute")).toBe("public");
    expect(resolveShellContext(undefined)).toBe("public");
  });

  it("returns workspace for authenticated task routes", () => {
    expect(resolveShellContext(ROUTE_NAME.USER_CENTER)).toBe("workspace");
    expect(resolveShellContext(ROUTE_NAME.AGENT_SUBMIT)).toBe("workspace");
    expect(resolveShellContext(ROUTE_NAME.USER_PROFILE)).toBe("workspace");
  });

  it("matches only workspace route names", () => {
    expect(isWorkspaceRouteName(ROUTE_NAME.EVALUATION_DETAIL)).toBe(true);
    expect(isWorkspaceRouteName(ROUTE_NAME.LEADERBOARD_PAGE)).toBe(false);
    expect(isWorkspaceRouteName(undefined)).toBe(false);
  });
});
