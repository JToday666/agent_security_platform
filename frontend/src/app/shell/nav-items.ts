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

export const EXPLORE_NAV_ITEMS: AppNavItem[] = [
  {
    key: "home",
    label: "首页",
    icon: "lucide:house",
    to: RouteLocation.home,
    exact: true,
  },
  {
    key: "dataset",
    label: "数据集目录",
    icon: "lucide:database",
    to: RouteLocation.datasetList,
  },
  {
    key: "leaderboard",
    label: "排行榜",
    icon: "lucide:trophy",
    to: RouteLocation.leaderboard,
  },
  {
    key: "contact",
    label: "联系我们",
    icon: "lucide:mail",
    to: RouteLocation.contact,
  },
];

export const WORKSPACE_NAV_ITEMS: AppNavItem[] = [
  {
    key: "records",
    label: "评测记录",
    icon: "lucide:clipboard-list",
    to: RouteLocation.userCenter,
    requiresAuth: true,
    exact: true,
  },
  {
    key: "agents",
    label: "智能体管理",
    icon: "lucide:bot",
    to: RouteLocation.agentManagement,
    requiresAuth: true,
  },
  {
    key: "register-agent",
    label: "注册智能体",
    icon: "lucide:bot-message-square",
    to: RouteLocation.agentRegister(),
    requiresAuth: true,
  },
  {
    key: "submit",
    label: "提交评测",
    icon: "lucide:file-plus-2",
    to: RouteLocation.agentSubmit,
    requiresAuth: true,
  },
];

export const WORKSPACE_SIDEBAR_ITEMS: AppNavItem[] = [
  ...WORKSPACE_NAV_ITEMS,
  {
    key: "profile",
    label: "个人资料",
    icon: "lucide:square-pen",
    to: RouteLocation.userProfile,
    requiresAuth: true,
  },
];
