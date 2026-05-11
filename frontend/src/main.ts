import { createApp } from "vue";
import App from "./App.vue";
import { createPinia } from "pinia";
import i18n from "./app/i18n";
import router from "./app/router/router";
import { useUserStore } from "./modules/account/stores/userStore";
import { ROUTE_NAME, RouteLocation } from "./app/router/route-names";
import "./app/styles/main.scss";

const app = createApp(App);
const pinia = createPinia();
app.use(pinia);
app.use(i18n);

const userStore = useUserStore(pinia);

let handlingUnauthorized = false;

// 全局未授权事件统一回退到首页，并唤起登录弹窗。
window.addEventListener("unauthorized", (event: Event) => {
  if (handlingUnauthorized) return;
  handlingUnauthorized = true;

  const customEvent = event as CustomEvent<{ message?: string }>;
  const message =
    customEvent.detail?.message ||
    i18n.global.t("auth.session.expiredMessage");
  const hadAuth = Boolean(userStore.token || userStore.currentUser);
  const isHomePage = router.currentRoute.value.name === ROUTE_NAME.HOME_PAGE;

  if (!isHomePage) {
    userStore.setPostLoginRedirect(router.currentRoute.value.fullPath);
  }

  userStore.logout();
  userStore.openLoginDialog();

  if (!isHomePage) {
    void router.push(RouteLocation.home);
  }

  if (hadAuth) {
    window.alert(message);
  }

  setTimeout(() => {
    handlingUnauthorized = false;
  }, 0);
});

// 在应用启动时开始拉取登录状态，但不阻塞路由和初次渲染。
userStore.restoreLogin().catch(() => {});

app.use(router);
await router.isReady();
app.mount("#app");
