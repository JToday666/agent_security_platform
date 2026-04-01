import type { RouteRecordRaw } from "vue-router";
import UserLayout from "@/layouts/UserLayout.vue";
import EvaluationReport from "@/views/EvaluationReport.vue";
import ProfilePage from "@/views/ProfilePage.vue";
import SubmitAgent from "@/views/SubmitAgentPage.vue";
import UserCenter from "@/views/UserCenter.vue";
import { ROUTE_NAME } from "@/router/RouteNames";

// 需要登录态的用户页面统一挂在用户布局下。
export const userRoutes: RouteRecordRaw[] = [
  {
    path: "/",
    component: UserLayout,
    meta: { requiresAuth: true },
    children: [
      {
        path: "user",
        name: ROUTE_NAME.USER_CENTER,
        component: UserCenter,
        meta: { requiresAuth: true, title: "评测记录" },
      },
      {
        path: "user/evaluation/:evaluationId",
        name: ROUTE_NAME.EVALUATION_DETAIL,
        component: EvaluationReport,
        meta: { requiresAuth: true, title: "评测详情" },
      },
      {
        path: "user/submit",
        name: ROUTE_NAME.AGENT_SUBMIT,
        component: SubmitAgent,
        meta: { requiresAuth: true, title: "提交智能体" },
      },
      {
        path: "user/profile",
        name: ROUTE_NAME.USER_PROFILE,
        component: ProfilePage,
        meta: { requiresAuth: true, title: "修改信息" },
      },
    ],
  },
];
