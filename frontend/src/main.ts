import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";
import { createPinia } from "pinia";
import { useUserStore } from "./store/user";
import "./styles/tokens.css";
import "./styles/primitives.css";
import "./styles/semantic.css";

const app = createApp(App);
const pinia = createPinia();
app.use(pinia);

const userStore = useUserStore(pinia);

let handlingUnauthorized = false;

window.addEventListener("unauthorized", (event: Event) => {
  if (handlingUnauthorized) return;
  handlingUnauthorized = true;

  const customEvent = event as CustomEvent<{ message?: string }>;
  const message = customEvent.detail?.message || "登录状态已失效，请重新登录";
  const hadAuth = Boolean(userStore.token || userStore.currentUser);

  userStore.logout();
  userStore.openLoginDialog();

  if (router.currentRoute.value.path !== "/") {
    void router.push("/");
  }

  if (hadAuth) {
    window.alert(message);
  }

  setTimeout(() => {
    handlingUnauthorized = false;
  }, 0);
});

// 在应用启动时恢复登录状态，避免刷新后路由守卫误拦截
await userStore.restoreLogin();

app.use(router);
await router.isReady();
app.mount("#app");
