import type { RouteRecordRaw } from "vue-router";
import PublicLayout from "@/app/layouts/PublicLayout.vue";
import { resolveLocalePath, resolveRuntimePreferredLocale } from "@/app/i18n";
import { ROUTE_NAME } from "@/app/router/route-names";

export const localeRootRedirectRoute: RouteRecordRaw = {
  path: "/",
  redirect: () => resolveLocalePath("/", resolveRuntimePreferredLocale()).path,
};

export const publicRoutes: RouteRecordRaw[] = [
  {
    path: "/:locale",
    component: PublicLayout,
    children: [
      {
        path: "",
        name: ROUTE_NAME.HOME_PAGE,
        component: () => import("@/modules/public/pages/HomePage.vue"),
      },
      {
        path: "attack-scenarios",
        name: ROUTE_NAME.ATTACK_SCENARIO_LIBRARY,
        component: () =>
          import(
            "@/modules/attack-scenario-library/pages/AttackScenarioCatalogPage.vue"
          ),
        meta: { restoreSessionScroll: true },
      },
      {
        path: "attack-scenarios/evaluation-items/:evaluationItemId",
        name: ROUTE_NAME.EVALUATION_ITEM_DETAIL,
        component: () =>
          import(
            "@/modules/attack-scenario-library/pages/EvaluationItemDetailPage.vue"
          ),
        meta: { restoreSessionScroll: true },
      },
      {
        path: "leaderboard",
        name: ROUTE_NAME.LEADERBOARD_PAGE,
        component: () =>
          import("@/modules/leaderboard/pages/LeaderboardPage.vue"),
      },
      {
        path: "contact",
        name: ROUTE_NAME.CONTACT_PAGE,
        component: () => import("@/modules/public/pages/ContactPage.vue"),
      },
    ],
  },
];

export const notFoundRoute: RouteRecordRaw = {
  path: "/:locale/:pathMatch(.*)*",
  component: PublicLayout,
  children: [
    {
      path: "",
      name: ROUTE_NAME.NOT_FOUND,
      component: () => import("@/modules/public/pages/NotFoundPage.vue"),
    },
  ],
};
