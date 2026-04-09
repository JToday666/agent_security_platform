import { createRouter, createWebHistory } from "vue-router";
import { registerRouteGuards } from "@/app/router/RouteGuards";
import { notFoundRoute, publicRoutes } from "@/app/router/modules/PublicRoutes";
import { userRoutes } from "@/app/router/modules/UserRoutes";

const router = createRouter({
  history: createWebHistory(),
  routes: [...publicRoutes, ...userRoutes, notFoundRoute],
  scrollBehavior(_to, _from, savedPosition) {
    if (savedPosition) {
      return savedPosition;
    }

    return { left: 0, top: 0 };
  },
});

registerRouteGuards(router);

export default router;
