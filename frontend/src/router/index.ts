import { createRouter, createWebHistory } from "vue-router";
import { registerRouteGuards } from "@/router/RouteGuards";
import { legacyRoutes } from "@/router/modules/LegacyRoutes";
import { publicRoutes } from "@/router/modules/PublicRoutes";
import { userRoutes } from "@/router/modules/UserRoutes";

const router = createRouter({
  history: createWebHistory(),
  routes: [...legacyRoutes, ...publicRoutes, ...userRoutes],
  scrollBehavior(_to, _from, savedPosition) {
    if (savedPosition) {
      return savedPosition;
    }

    return { left: 0, top: 0 };
  },
});

registerRouteGuards(router);

export default router;
