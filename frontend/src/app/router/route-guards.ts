import type { Router } from "vue-router";
import {
  activateLocale,
  resolveLocalePath,
  resolveRuntimePreferredLocale,
} from "@/app/i18n";
import { RouteLocation } from "@/app/router/route-names";
import { useUserStore } from "@/modules/account/stores/userStore";

// 集中注册全局守卫，避免在 router 入口文件里堆积业务逻辑。
export const registerRouteGuards = (router: Router) => {
  router.beforeEach(async (to) => {
    const localePath = resolveLocalePath(
      to.fullPath,
      resolveRuntimePreferredLocale(),
    );

    if (localePath.redirect) {
      return localePath.path;
    }

    const activeLocale = await activateLocale(localePath.locale);
    RouteLocation.setCurrentLocale(activeLocale);

    const userStore = useUserStore();
    const requiresAuth = to.matched.some((record) => record.meta.requiresAuth);

    if (requiresAuth) {
      if (userStore.initPromise) {
        await userStore.initPromise;
      }

      if (!userStore.isLogin) {
        // 登录成功后仍然回到原始目标页，而不是固定回到用户中心。
        userStore.setPostLoginRedirect(to.fullPath);
        userStore.openLoginDialog();
        return RouteLocation.home;
      }
    }

    return true;
  });
};
