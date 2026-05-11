import type { RouteLocationRaw } from "vue-router";
import { RouteLocation } from "@/app/router/route-names";

export interface AppNavItem {
  key: string;
  label: string;
  icon: string;
  to: RouteLocationRaw;
  requiresAuth?: boolean;
  exact?: boolean;
}

type Translate = (key: string) => string;

export const buildExploreNavItems = (t: Translate): AppNavItem[] => [
  {
    key: "home",
    label: t("layout.nav.home"),
    icon: "lucide:house",
    to: RouteLocation.home,
    exact: true,
  },
  {
    key: "dataset",
    label: t("layout.nav.dataset"),
    icon: "lucide:database",
    to: RouteLocation.datasetList,
  },
  {
    key: "leaderboard",
    label: t("layout.nav.leaderboard"),
    icon: "lucide:trophy",
    to: RouteLocation.leaderboard,
  },
  {
    key: "contact",
    label: t("layout.nav.contact"),
    icon: "lucide:mail",
    to: RouteLocation.contact,
  },
];

export const buildWorkspaceNavItems = (t: Translate): AppNavItem[] => [
  {
    key: "records",
    label: t("layout.nav.records"),
    icon: "lucide:clipboard-list",
    to: RouteLocation.userCenter,
    requiresAuth: true,
    exact: true,
  },
  {
    key: "agents",
    label: t("layout.nav.agents"),
    icon: "lucide:bot",
    to: RouteLocation.agentManagement,
    requiresAuth: true,
  },
  {
    key: "register-agent",
    label: t("layout.nav.registerAgent"),
    icon: "lucide:bot-message-square",
    to: RouteLocation.agentRegister(),
    requiresAuth: true,
  },
  {
    key: "submit",
    label: t("layout.nav.submit"),
    icon: "lucide:file-plus-2",
    to: RouteLocation.agentSubmit,
    requiresAuth: true,
  },
];

export const buildWorkspaceSidebarItems = (t: Translate): AppNavItem[] => [
  ...buildWorkspaceNavItems(t),
  {
    key: "profile",
    label: t("layout.nav.profile"),
    icon: "lucide:square-pen",
    to: RouteLocation.userProfile,
    requiresAuth: true,
  },
];
