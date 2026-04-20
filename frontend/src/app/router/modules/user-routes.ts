import type { RouteRecordRaw } from "vue-router";
import UserLayout from "@/app/layouts/UserLayout.vue";
import { ROUTE_NAME } from "@/app/router/route-names";
import ProfilePage from "@/modules/account/pages/ProfilePage.vue";
import EvaluationDetailPage from "@/modules/evaluation/pages/EvaluationDetailPage.vue";
import EvaluationRecordsPage from "@/modules/evaluation/pages/EvaluationRecordsPage.vue";
import SubmitAgentPage from "@/modules/submission/pages/SubmitAgentPage.vue";

export const userRoutes: RouteRecordRaw[] = [
  {
    path: "/",
    component: UserLayout,
    meta: { requiresAuth: true },
    children: [
      {
        path: "user",
        name: ROUTE_NAME.USER_CENTER,
        component: EvaluationRecordsPage,
        meta: { requiresAuth: true },
      },
      {
        path: "user/evaluation/:evaluationId",
        name: ROUTE_NAME.EVALUATION_DETAIL,
        component: EvaluationDetailPage,
        meta: { requiresAuth: true },
      },
      {
        path: "user/submit",
        name: ROUTE_NAME.AGENT_SUBMIT,
        component: SubmitAgentPage,
        meta: { requiresAuth: true },
      },
      {
        path: "user/profile",
        name: ROUTE_NAME.USER_PROFILE,
        component: ProfilePage,
        meta: { requiresAuth: true },
      },
    ],
  },
];
