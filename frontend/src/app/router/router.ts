import {
  createRouter,
  createWebHistory,
  type RouteLocationNormalizedLoaded,
} from "vue-router";
import { registerRouteGuards } from "@/app/router/route-guards";
import {
  notFoundRoute,
  publicRoutes,
} from "@/app/router/modules/public-routes";
import { userRoutes } from "@/app/router/modules/user-routes";
import {
  buildSessionScrollStorageKey,
  loadSessionScrollPosition,
  saveSessionScrollPosition,
} from "@/shared/lib/session-scroll-state";

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
