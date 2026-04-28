import type { RouteRecordRaw } from "vue-router";
import UserLayout from "@/app/layouts/UserLayout.vue";
import { ROUTE_NAME } from "@/app/router/route-names";
import ProfilePage from "@/modules/account/pages/ProfilePage.vue";
import AgentDetailPage from "@/modules/agent/pages/AgentDetailPage.vue";
import AgentManagementPage from "@/modules/agent/pages/AgentManagementPage.vue";
import AgentRegisterPage from "@/modules/agent/pages/AgentRegisterPage.vue";
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
        path: "user/agents",
        name: ROUTE_NAME.AGENT_MANAGEMENT,
        component: AgentManagementPage,
        meta: { requiresAuth: true },
      },
      {
        path: "user/agents/register",
        name: ROUTE_NAME.AGENT_REGISTER,
        component: AgentRegisterPage,
        meta: { requiresAuth: true },
      },
      {
        path: "user/agents/:agentId",
        name: ROUTE_NAME.AGENT_DETAIL,
        component: AgentDetailPage,
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
