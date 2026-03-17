<template>
	<div class="report-card ui-surface-glass">
		<h1 class="page-title">评估报告</h1>
		<p class="report-id">报告 ID：{{ id }}</p>

		<div class="summary-section ui-surface-white">
			<div class="summary-item">
				<span class="label">智能体名称</span>
				<span class="value">{{ report.agentName }}</span>
			</div>
			<div class="summary-item">
				<span class="label">评估数据集</span>
				<span class="value">{{ report.dataset }}</span>
			</div>
			<div class="summary-item">
				<span class="label">评估时间</span>
				<span class="value">{{ report.date }}</span>
			</div>
			<div class="summary-item">
				<span class="label">综合得分</span>
				<span class="value score">{{ report.score }}</span>
			</div>
		</div>

		<h2 class="section-title">详细指标</h2>
		<div class="metrics-grid">
			<div v-for="metric in report.metrics" :key="metric.name" class="metric-item ui-surface-white">
				<div class="metric-header">
					<span class="metric-name">{{ metric.name }}</span>
					<span class="metric-value">{{ metric.value }}</span>
				</div>
				<div class="progress-bar">
					<div class="progress-fill" :style="{ width: metric.percentage + '%' }"></div>
				</div>
				<p class="metric-desc">{{ metric.description }}</p>
			</div>
		</div>

		<div class="remarks" v-if="report.remarks">
			<h3>备注</h3>
			<p>{{ report.remarks }}</p>
		</div>

		<div class="actions">
			<button class="back-btn ui-btn ui-btn-pill" @click="goBack">← 返回评估记录</button>
		</div>
	</div>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from "vue-router";
import { computed } from "vue";

const route = useRoute();
const router = useRouter();
const id = route.params.id as string;

const report = computed(() => {
	return {
		agentName: "智能体 Alpha-1",
		dataset: "Prompt Injection Dataset",
		date: "2025-02-15",
		score: 92.5,
		metrics: [
			{
				name: "攻击检测率",
				value: "94%",
				percentage: 94,
				description: "成功识别提示注入攻击的比率",
			},
			{
				name: "误报率",
				value: "3%",
				percentage: 3,
				description: "正常请求被误判为攻击的比率",
			},
			{
				name: "响应时间",
				value: "1.2s",
				percentage: 85,
				description: "平均响应时间（越低越好）",
			},
			{
				name: "鲁棒性",
				value: "89%",
				percentage: 89,
				description: "对抗样本下的正确率",
			},
		],
		remarks:
			"本次评测共执行 500 次攻击测试，智能体表现良好，但在复杂越狱场景下仍有提升空间。",
	};
});

const goBack = () => {
	router.push("/user");
};
</script>

<style scoped>
/* 全局重置动画 */
.report-card {
	border-radius: 2rem;
	padding: 2.5rem;
	max-width: 800px;
	margin: 0 auto;
}

.page-title {
	font-size: 2.5rem;
	font-weight: 700;
	margin-bottom: 0.5rem;
}

.report-id {
	font-size: 1rem;
	color: #64748b;
	margin-bottom: 2rem;
	padding-bottom: 1rem;
	border-bottom: 1px solid #e2e8f0;
}

.summary-section {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
	gap: 1.5rem;
	border-radius: 1.2rem;
	padding: 1.5rem;
	margin-bottom: 2rem;
}

.summary-item {
	display: flex;
	flex-direction: column;
}

.label {
	font-size: 0.85rem;
	text-transform: uppercase;
	letter-spacing: 0.5px;
	color: #64748b;
	margin-bottom: 0.3rem;
}

.value {
	font-size: 1.3rem;
	font-weight: 600;
	color: #0f172a;
}

.score {
	color: #f59e0b;
	font-size: 1.8rem;
	font-weight: 700;
}

.section-title {
	font-size: 1.5rem;
	font-weight: 600;
	margin: 2rem 0 1rem;
	color: #0f172a;
}

.metrics-grid {
	display: flex;
	flex-direction: column;
	gap: 1.2rem;
	margin-bottom: 2rem;
}

.metric-item {
	padding: 1.2rem;
	border-radius: 1rem;
	transition:
		transform 0.2s,
		box-shadow 0.2s;
}

.metric-item:hover {
	transform: translateY(-2px);
	box-shadow: 0 15px 25px -8px rgba(0, 0, 0, 0.1);
}

.metric-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 0.5rem;
}

.metric-name {
	font-weight: 600;
	font-size: 1.1rem;
	color: #0f172a;
}

.metric-value {
	font-weight: 700;
	color: #2563eb;
}

.progress-bar {
	width: 100%;
	height: 8px;
	background: #e2e8f0;
	border-radius: 4px;
	margin-bottom: 0.5rem;
	overflow: hidden;
}

.progress-fill {
	height: 100%;
	background: var(--grad-progress);
	border-radius: 4px;
	transition: width 0.3s ease;
}

.metric-desc {
	font-size: 0.9rem;
	color: #64748b;
	margin: 0;
}

.remarks {
	background: white;
	padding: 1.2rem;
	border-radius: 1rem;
	margin: 2rem 0;
	border-left: 4px solid #2563eb;
	box-shadow: 0 5px 15px -5px rgba(0, 0, 0, 0.05);
}

.remarks h3 {
	font-size: 1.1rem;
	margin-bottom: 0.5rem;
	font-weight: 600;
	color: #0f172a;
}

.remarks p {
	margin: 0;
	line-height: 1.6;
	color: #475569;
}

.actions {
	margin-top: 2rem;
	text-align: center;
}

.back-btn {
	padding: 0.8rem 2rem;
	font-size: 1rem;
	font-weight: 500;
}

.back-btn:hover {
	background: #f8fafc;
	border-color: #94a3b8;
	transform: translateX(-5px);
	box-shadow: 0 8px 16px -6px rgba(0, 0, 0, 0.1);
}

/* 移动端适配 */
@media (max-width: 768px) {
	.report-card {
		padding: 1.5rem;
	}

	.summary-section {
		grid-template-columns: 1fr 1fr;
		gap: 1rem;
		padding: 1rem;
	}

	.score {
		font-size: 1.5rem;
	}
}
</style>
