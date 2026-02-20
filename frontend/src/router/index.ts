import { createRouter, createWebHistory } from "vue-router";
import Home from "@/views/HomePage.vue";
import DataSet from "@/views/DataSet.vue";
import DatasetDetail from "@/views/DatasetDetail.vue";
import LeaderBoard from "@/views/LeaderBoard.vue";
import UserCenter from "@/views/UserCenter.vue";
import EvaluationReport from "@/views/EvaluationReport.vue";
import SubmitAgent from "@/views/SubmitAgent.vue";
import ProfilePage from "@/views/ProfilePage.vue";
import ContactUs from "@/views/ContactUs.vue";
import { useUserStore } from "@/store/user";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", component: Home },
    { path: "/dataset", component: DataSet },
    { path: "/dataset/:id", component: DatasetDetail },
    { path: "/leaderboard", component: LeaderBoard },
    { path: "/contact", component: ContactUs },

    {
      path: "/user",
      component: UserCenter,
      meta: { requiresAuth: true },
    },
    {
      path: "/report/:id",
      component: EvaluationReport,
      meta: { requiresAuth: true },
    },
    {
      path: "/submit",
      component: SubmitAgent,
      meta: { requiresAuth: true },
    },
    {
      path: "/profile",
      component: ProfilePage,
      meta: { requiresAuth: true },
    },
  ],
});

router.beforeEach((to, _, next) => {
  const userStore = useUserStore();

  if (to.meta.requiresAuth && !userStore.isLogin) {
    userStore.showLogin = true;
    next(false);
  } else {
    next();
  }
});

export default router;
