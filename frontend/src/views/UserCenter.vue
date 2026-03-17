<template>
	<div class="records-card ui-surface-glass">
		<h1 class="page-title">评估记录</h1>
		<p class="page-subtitle">您提交过的所有智能体评估记录。</p>

		<div class="records-list">
			<div v-for="record in records" :key="record.id" class="record-item ui-surface-white">
				<div class="record-info">
					<h3>{{ record.name }}</h3>
					<p>数据集：{{ record.dataset }} · 提交时间：{{ record.date }}</p>
				</div>
				<router-link :to="`/report/${record.id}`"
					class="view-btn ui-btn ui-btn-pill ui-btn-gradient ui-btn-hover-lift">
					查看报告 ←
				</router-link>
			</div>
		</div>

		<div v-if="records.length === 0" class="empty-state">
			<p>您还没有提交过智能体评估。</p>
			<router-link to="/submit"
				class="btn ui-btn ui-btn-pill ui-btn-gradient ui-btn-hover-lift">立即提交</router-link>
		</div>
	</div>
</template>

<script setup lang="ts">
const records = [
	{
		id: 1,
		name: "智能体 Alpha-1",
		dataset: "Prompt Injection Dataset",
		date: "2025-02-10",
	},
	{
		id: 2,
		name: "智能体 Beta-2",
		dataset: "Jailbreak Dataset",
		date: "2025-02-12",
	},
];
</script>

<style scoped>
.records-card {
	border-radius: 2rem;
	padding: 2rem 2.5rem;
	max-width: 900px;
	margin: 0 auto;
}

.page-title {
	font-size: 2.5rem;
	font-weight: 700;
	margin-bottom: 0.5rem;
}

.page-subtitle {
	font-size: 1.1rem;
	margin-bottom: 2rem;
}

.records-list {
	display: flex;
	flex-direction: column;
	gap: 1rem;
}

.record-item {
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 1.2rem 1.5rem;
	border-radius: 1.2rem;
	transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.record-item:hover {
	transform: translateX(5px);
	box-shadow: 0 20px 30px -10px rgba(0, 0, 0, 0.15);
}

.record-info h3 {
	font-size: 1.3rem;
	font-weight: 600;
	margin-bottom: 0.3rem;
	color: #0f172a;
}

.record-info p {
	font-size: 0.95rem;
	color: #64748b;
}

.view-btn {
	padding: 0.5rem 1.2rem;
	text-decoration: none;
	font-weight: 500;
	transition:
		transform 0.2s,
		box-shadow 0.2s;
}

.empty-state {
	text-align: center;
	padding: 3rem 0;
}

.empty-state p {
	font-size: 1.1rem;
	color: #475569;
	margin-bottom: 1.5rem;
}

.btn {
	display: inline-block;
	padding: 0.8rem 2rem;
	text-decoration: none;
	font-weight: 600;
	transition:
		transform 0.2s,
		box-shadow 0.2s;
}

@media (max-width: 768px) {
	.records-card {
		padding: 1.5rem;
	}

	.page-title {
		font-size: 2rem;
	}

	.record-item {
		flex-direction: column;
		align-items: flex-start;
		gap: 1rem;
	}

	.view-btn {
		align-self: flex-end;
	}
}
</style>
