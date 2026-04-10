import {
  createRouter,
  createWebHistory,
  type RouteLocationNormalizedLoaded,
} from "vue-router";
import { registerRouteGuards } from "@/app/router/RouteGuards";
import { notFoundRoute, publicRoutes } from "@/app/router/modules/PublicRoutes";
import { userRoutes } from "@/app/router/modules/UserRoutes";
import {
  buildSessionScrollStorageKey,
  loadSessionScrollPosition,
  saveSessionScrollPosition,
} from "@/shared/lib/SessionScrollState";

const resolveSessionScrollKey = (
  route: RouteLocationNormalizedLoaded,
): string | null => {
  if (!route.name) {
    return null;
  }

  const routeMeta = route.meta as { restoreSessionScroll?: boolean };
  if (!routeMeta.restoreSessionScroll) {
    return null;
  }

  return buildSessionScrollStorageKey(String(route.name), route.params);
};

const router = createRouter({
  history: createWebHistory(),
  routes: [...publicRoutes, ...userRoutes, notFoundRoute],
  scrollBehavior(to, _from, savedPosition) {
    if (savedPosition) {
      return savedPosition;
    }

    const sessionScrollKey = resolveSessionScrollKey(to);
    if (sessionScrollKey) {
      const restoredPosition = loadSessionScrollPosition(
        sessionStorage,
        sessionScrollKey,
      );
      if (restoredPosition) {
        return restoredPosition;
      }
    }

    return { left: 0, top: 0 };
  },
});

registerRouteGuards(router);

router.beforeEach((_to, from) => {
  const fromScrollKey = resolveSessionScrollKey(from);
  if (fromScrollKey) {
    saveSessionScrollPosition(sessionStorage, fromScrollKey, window.scrollY);
  }
});

export default router;
