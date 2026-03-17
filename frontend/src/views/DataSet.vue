<template>
	<div class="content">
		<h1 class="page-title">数据集列表</h1>
		<p class="page-subtitle">选择以下数据集，查看详细说明和下载链接。</p>

		<div class="dataset-grid">
			<router-link v-for="item in datasets" :key="item.id" :to="`/dataset/${item.id}`"
				class="dataset-card ui-surface-glass">
				<h3>{{ item.name }}</h3>
				<p>{{ item.description }}</p>
				<span class="card-link">查看详情 →</span>
			</router-link>
		</div>
	</div>
</template>

<script setup lang="ts">
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
.content {
	max-width: 1200px;
	padding: 3rem 2rem;
	color: #1e293b;
	/* 深色文字 */
}

.page-title {
	font-size: 3rem;
	font-weight: 800;
	margin-bottom: 0.5rem;
}

.page-subtitle {
	font-size: 1.2rem;
	margin-bottom: 3rem;
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
