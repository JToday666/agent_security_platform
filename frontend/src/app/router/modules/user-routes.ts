import type { RouteRecordRaw } from "vue-router";
import UserLayout from "@/app/layouts/UserLayout.vue";
import { ROUTE_NAME } from "@/app/router/route-names";

export const userRoutes: RouteRecordRaw[] = [
  {
    path: "/",
    component: UserLayout,
    meta: { requiresAuth: true },
    children: [
      {
        path: "user",
        name: ROUTE_NAME.USER_CENTER,
        component: () =>
          import("@/modules/evaluation/pages/EvaluationRecordsPage.vue"),
        meta: { requiresAuth: true },
      },
      {
        path: "user/evaluation/:evaluationId",
        name: ROUTE_NAME.EVALUATION_DETAIL,
        component: () =>
          import("@/modules/evaluation/pages/EvaluationDetailPage.vue"),
        meta: { requiresAuth: true },
      },
      {
        path: "user/agents",
        name: ROUTE_NAME.AGENT_MANAGEMENT,
        component: () =>
          import("@/modules/agent/pages/AgentManagementPage.vue"),
        meta: { requiresAuth: true },
      },
      {
        path: "user/agents/register",
        name: ROUTE_NAME.AGENT_REGISTER,
        component: () => import("@/modules/agent/pages/AgentRegisterPage.vue"),
        meta: { requiresAuth: true },
      },
      {
        path: "user/agents/:agentId",
        name: ROUTE_NAME.AGENT_DETAIL,
        component: () => import("@/modules/agent/pages/AgentDetailPage.vue"),
        meta: { requiresAuth: true },
      },
      {
        path: "user/submit",
        name: ROUTE_NAME.AGENT_SUBMIT,
        component: () =>
          import("@/modules/submission/pages/SubmitAgentPage.vue"),
        meta: { requiresAuth: true },
      },
      {
        path: "user/profile",
        name: ROUTE_NAME.USER_PROFILE,
        component: () => import("@/modules/account/pages/ProfilePage.vue"),
        meta: { requiresAuth: true },
      },
    ],
  },
];
