import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";
import { createPinia } from "pinia";
import { useUserStore } from "./store/user";

const app = createApp(App);

const pinia = createPinia();
app.use(pinia);
app.use(router);

// 在应用启动时初始化登录状态
const userStore = useUserStore();
userStore
  .initAuth()
  .catch(() => {
    // 初始化失败时由 store 自行处理状态兜底
  })
  .finally(() => {
    app.mount("#app");
  });
