import type { RouteRecordRaw } from "vue-router";
import PublicLayout from "@/layouts/PublicLayout.vue";
import ContactUs from "@/views/ContactUs.vue";
import DatasetDetail from "@/views/DatasetDetail.vue";
import DatasetCatalogPage from "@/views/DatasetCatalogPage.vue";
import HomePage from "@/views/HomePage.vue";
import LeaderboardPage from "@/views/LeaderboardPage.vue";
import { ROUTE_NAME } from "@/router/RouteNames";

// 公共页面路由统一挂在公共布局下。
export const publicRoutes: RouteRecordRaw[] = [
  {
    path: "/",
    component: PublicLayout,
    children: [
      {
        path: "",
        name: ROUTE_NAME.HOME_PAGE,
        component: HomePage,
        meta: { title: "首页" },
      },
      {
        path: "dataset",
        name: ROUTE_NAME.DATASET_LIST,
        component: DatasetCatalogPage,
        meta: { title: "数据集" },
      },
      {
        path: "dataset/:datasetId",
        name: ROUTE_NAME.DATASET_DETAIL,
        component: DatasetDetail,
        meta: { title: "数据集详情" },
      },
      {
        path: "leaderboard",
        name: ROUTE_NAME.LEADERBOARD_PAGE,
        component: LeaderboardPage,
        meta: { title: "排行榜" },
      },
      {
        path: "contact",
        name: ROUTE_NAME.CONTACT_PAGE,
        component: ContactUs,
        meta: { title: "联系我们" },
      },
    ],
  },
];
