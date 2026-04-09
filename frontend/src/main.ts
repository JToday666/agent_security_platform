import { createApp } from "vue";
import App from "./App.vue";
import { createPinia } from "pinia";
import router from "./app/router";
import { useUserStore } from "./modules/account/stores/UserStore";
import { RouteLocation } from "./app/router/RouteNames";
import "./app/styles";

const app = createApp(App);
const pinia = createPinia();
app.use(pinia);

const userStore = useUserStore(pinia);

let handlingUnauthorized = false;

// 全局未授权事件统一回退到首页，并唤起登录弹窗。
window.addEventListener("unauthorized", (event: Event) => {
  if (handlingUnauthorized) return;
  handlingUnauthorized = true;

  const customEvent = event as CustomEvent<{ message?: string }>;
  const message = customEvent.detail?.message || "登录状态已失效，请重新登录";
  const hadAuth = Boolean(userStore.token || userStore.currentUser);

  if (router.currentRoute.value.path !== "/") {
    userStore.setPostLoginRedirect(router.currentRoute.value.fullPath);
  }

  userStore.logout();
  userStore.openLoginDialog();

  if (router.currentRoute.value.path !== "/") {
    void router.push(RouteLocation.home);
  }

  if (hadAuth) {
    window.alert(message);
  }

  setTimeout(() => {
    handlingUnauthorized = false;
  }, 0);
});

// 在应用启动时恢复登录状态，避免刷新后路由守卫误拦截。
await userStore.restoreLogin();

app.use(router);
await router.isReady();
app.mount("#app");
