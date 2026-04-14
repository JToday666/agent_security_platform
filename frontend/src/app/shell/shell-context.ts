import { ROUTE_NAME, type AppRouteName } from "../router/route-names";

const WORKSPACE_ROUTE_NAMES = new Set<AppRouteName>([
  ROUTE_NAME.USER_CENTER,
  ROUTE_NAME.EVALUATION_DETAIL,
  ROUTE_NAME.AGENT_SUBMIT,
  ROUTE_NAME.USER_PROFILE,
]);

export type ShellContext = "public" | "workspace";

export const isWorkspaceRouteName = (
  routeName?: string | null,
): routeName is AppRouteName =>
  routeName !== undefined &&
  routeName !== null &&
  WORKSPACE_ROUTE_NAMES.has(routeName as AppRouteName);

export const resolveShellContext = (routeName?: string | null): ShellContext =>
  isWorkspaceRouteName(routeName) ? "workspace" : "public";
