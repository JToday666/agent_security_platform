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
import PublicLayout from "@/layouts/PublicLayout.vue";
import UserLayout from "@/layouts/UserLayout.vue";
import { useUserStore } from "@/store/user";

const router = createRouter({
	history: createWebHistory(),
	routes: [
		{
			path: "/",
			component: PublicLayout,
			children: [
				{ path: "", component: Home },
				{ path: "dataset", component: DataSet },
				{ path: "dataset/:id", component: DatasetDetail },
				{ path: "leaderboard", component: LeaderBoard },
				{ path: "contact", component: ContactUs },
			],
		},

		{
			path: "/",
			component: UserLayout,
			meta: { requiresAuth: true },
			children: [
				{
					path: "user",
					component: UserCenter,
				},
				{
					path: "report/:id",
					component: EvaluationReport,
				},
				{
					path: "submit",
					component: SubmitAgent,
				},
				{
					path: "profile",
					component: ProfilePage,
				},
			],
		},
	],
});

router.beforeEach((to, _, next) => {
	const userStore = useUserStore();
	const requiresAuth = to.matched.some((record) => record.meta.requiresAuth);

	if (requiresAuth && !userStore.isLogin) {
		userStore.showLogin = true;
		next(false);
	} else {
		next();
	}
});

export default router;
