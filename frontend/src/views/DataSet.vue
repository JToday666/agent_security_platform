<template>
	<Navbar />
	<main class="page-container dataset-page">
		<div class="content">
			<h1 class="page-title">数据集列表</h1>
			<p class="page-subtitle">选择以下数据集，查看详细说明和下载链接。</p>

			<div class="dataset-grid">
				<router-link
					v-for="item in datasets"
					:key="item.id"
					:to="`/dataset/${item.id}`"
					class="dataset-card"
				>
					<h3>{{ item.name }}</h3>
					<p>{{ item.description }}</p>
					<span class="card-link">查看详情 →</span>
				</router-link>
			</div>
		</div>
	</main>
</template>

<script setup lang="ts">
import Navbar from "@/components/NavBar.vue";

const datasets = [
	{
		id: 1,
		name: "Prompt Injection Dataset",
		description:
			"包含多种提示注入攻击样本，用于测试智能体对恶意指令的防御能力。",
	},
	{
		id: 2,
		name: "Jailbreak Dataset",
		description: "模拟越狱攻击场景，评估智能体在违规请求下的行为安全性。",
	},
	// 可以继续添加更多数据集
];
</script>

<style scoped>
/* 全局重置与动画 */
* {
	box-sizing: border-box;
}

@keyframes fadeInUp {
	from {
		opacity: 0;
		transform: translateY(30px);
	}

	to {
		opacity: 1;
		transform: translateY(0);
	}
}

.page-container {
	min-height: 100vh;
	padding-top: 80px;
	/* 为固定导航栏留出空间 */
	background: linear-gradient(145deg, #f8fafc 0%, #eef2f6 100%);
	display: flex;
	justify-content: center;
	position: relative;
	overflow: hidden;
}

/* 微弱的纹理背景 */
.page-container::before {
	content: "";
	position: absolute;
	width: 100%;
	height: 100%;
	background-image:
		radial-gradient(
			circle at 20% 30%,
			rgba(59, 130, 246, 0.03) 0%,
			transparent 30%
		),
		radial-gradient(
			circle at 80% 70%,
			rgba(236, 72, 153, 0.03) 0%,
			transparent 30%
		);
	pointer-events: none;
}

.content {
	max-width: 1200px;
	width: 100%;
	padding: 3rem 2rem;
	color: #1e293b;
	/* 深色文字 */
	position: relative;
	z-index: 2;
	animation: fadeInUp 0.8s ease;
}

.page-title {
	font-size: 3rem;
	font-weight: 800;
	margin-bottom: 0.5rem;
	background: linear-gradient(135deg, #2563eb, #7c3aed);
	-webkit-background-clip: text;
	background-clip: text;
	-webkit-text-fill-color: transparent;
	text-shadow: 0 5px 15px rgba(37, 99, 235, 0.15);
}

.page-subtitle {
	font-size: 1.2rem;
	color: #475569;
	margin-bottom: 3rem;
	line-height: 1.6;
}

.dataset-grid {
	display: grid;
	grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
	gap: 2rem;
}

.dataset-card {
	background: rgba(255, 255, 255, 0.7);
	backdrop-filter: blur(12px);
	-webkit-backdrop-filter: blur(12px);
	border-radius: 2rem;
	padding: 2rem;
	border: 1px solid rgba(255, 255, 255, 0.8);
	transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
	text-decoration: none;
	color: #1e293b;
	display: flex;
	flex-direction: column;
	box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05);
}

.dataset-card:hover {
	transform: translateY(-8px);
	box-shadow: 0 25px 40px -12px rgba(0, 0, 0, 0.2);
	background: rgba(255, 255, 255, 0.85);
	border-color: rgba(255, 255, 255, 0.9);
}

.dataset-card h3 {
	font-size: 1.8rem;
	font-weight: 600;
	margin-bottom: 0.8rem;
	color: #0f172a;
}

.dataset-card p {
	font-size: 1rem;
	line-height: 1.6;
	color: #475569;
	margin-bottom: 1.5rem;
	flex: 1;
}

.card-link {
	align-self: flex-end;
	font-weight: 600;
	color: #2563eb;
	transition:
		transform 0.2s,
		color 0.2s;
	display: inline-flex;
	align-items: center;
	gap: 0.4rem;
}

.dataset-card:hover .card-link {
	transform: translateX(4px);
	color: #7c3aed;
}

/* 响应式调整 */
@media (max-width: 640px) {
	.content {
		padding: 2rem 1rem;
	}

	.page-title {
		font-size: 2.5rem;
	}

	.page-subtitle {
		font-size: 1rem;
		margin-bottom: 2rem;
	}

	.dataset-grid {
		grid-template-columns: 1fr;
	}

	.dataset-card {
		padding: 1.5rem;
	}

	.dataset-card h3 {
		font-size: 1.5rem;
	}
}
</style>
