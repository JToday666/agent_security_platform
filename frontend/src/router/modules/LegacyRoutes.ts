import type { RouteRecordRaw } from "vue-router";

// 保留历史入口，避免已有书签和站内旧跳转失效。
export const legacyRoutes: RouteRecordRaw[] = [
  {
    path: "/submit",
    redirect: "/user/submit",
  },
  {
    path: "/report/:id",
    redirect: (to) => `/user/evaluation/${String(to.params.id ?? "")}`,
  },
  {
    path: "/profile",
    redirect: "/user/profile",
  },
];
