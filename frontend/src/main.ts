import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";
import { createPinia } from "pinia";
import { useUserStore } from "./store/user";

const app = createApp(App);

const pinia = createPinia();
app.use(pinia);
app.use(router);

// 在应用启动时恢复登录状态
const userStore = useUserStore();
userStore.restoreLogin();

app.mount("#app");
