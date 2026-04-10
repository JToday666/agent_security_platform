import type { RouteRecordRaw } from "vue-router";
import PublicLayout from "@/app/layouts/PublicLayout.vue";
import { ROUTE_NAME } from "@/app/router/RouteNames";
import ContactPage from "@/modules/public/pages/ContactPage.vue";
import DatasetCatalogPage from "@/modules/dataset/pages/DatasetCatalogPage.vue";
import DatasetDetailPage from "@/modules/dataset/pages/DatasetDetailPage.vue";
import HomePage from "@/modules/public/pages/HomePage.vue";
import LeaderboardPage from "@/modules/public/pages/LeaderboardPage.vue";
import NotFoundPage from "@/modules/public/pages/NotFoundPage.vue";

export const publicRoutes: RouteRecordRaw[] = [
  {
    path: "/",
    component: PublicLayout,
    children: [
      {
        path: "",
        name: ROUTE_NAME.HOME_PAGE,
        component: HomePage,
      },
      {
        path: "dataset",
        name: ROUTE_NAME.DATASET_LIST,
        component: DatasetCatalogPage,
        meta: { restoreSessionScroll: true },
      },
      {
        path: "dataset/:datasetId",
        name: ROUTE_NAME.DATASET_DETAIL,
        component: DatasetDetailPage,
        meta: { restoreSessionScroll: true },
      },
      {
        path: "leaderboard",
        name: ROUTE_NAME.LEADERBOARD_PAGE,
        component: LeaderboardPage,
      },
      {
        path: "contact",
        name: ROUTE_NAME.CONTACT_PAGE,
        component: ContactPage,
      },
    ],
  },
];

export const notFoundRoute: RouteRecordRaw = {
  path: "/:pathMatch(.*)*",
  component: PublicLayout,
  children: [
    {
      path: "",
      name: ROUTE_NAME.NOT_FOUND,
      component: NotFoundPage,
    },
  ],
};
