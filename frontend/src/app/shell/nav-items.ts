import type { RouteLocationRaw } from "vue-router";
import { RouteLocation } from "@/app/router/route-names";
import type { AppIconName } from "@/shared/ui/branding/app-icon-registry";

export interface AppNavItem {
  key: string;
  label: string;
  icon: AppIconName;
  to: RouteLocationRaw;
  requiresAuth?: boolean;
  exact?: boolean;
}

type Translate = (key: string) => string;

export const buildExploreNavItems = (t: Translate): AppNavItem[] => [
  {
    key: "home",
    label: t("layout.nav.home"),
    icon: "app:nav.home",
    to: RouteLocation.home,
    exact: true,
  },
  {
    key: "attack-scenarios",
    label: t("layout.nav.attackScenarioLibrary"),
    icon: "app:nav.attackScenarios",
    to: RouteLocation.attackScenarioLibrary,
  },
  {
    key: "leaderboard",
    label: t("layout.nav.leaderboard"),
    icon: "app:nav.leaderboard",
    to: RouteLocation.leaderboard,
  },
  {
    key: "contact",
    label: t("layout.nav.contact"),
    icon: "app:nav.contact",
    to: RouteLocation.contact,
  },
];

export const buildWorkspaceNavItems = (t: Translate): AppNavItem[] => [
  {
    key: "records",
    label: t("layout.nav.records"),
    icon: "app:nav.records",
    to: RouteLocation.userCenter,
    requiresAuth: true,
    exact: true,
  },
  {
    key: "agents",
    label: t("layout.nav.agents"),
    icon: "app:nav.agents",
    to: RouteLocation.agentManagement,
    requiresAuth: true,
  },
  {
    key: "register-agent",
    label: t("layout.nav.registerAgent"),
    icon: "app:nav.registerAgent",
    to: RouteLocation.agentRegister(),
    requiresAuth: true,
  },
  {
    key: "submit",
    label: t("layout.nav.submit"),
    icon: "app:nav.submit",
    to: RouteLocation.agentSubmit,
    requiresAuth: true,
  },
];

export const buildWorkspaceSidebarItems = (t: Translate): AppNavItem[] => [
  ...buildWorkspaceNavItems(t),
  {
    key: "profile",
    label: t("layout.nav.profile"),
    icon: "app:nav.profile",
    to: RouteLocation.userProfile,
    requiresAuth: true,
  },
];
