<template>
	<Navbar />
	<main class="page-container report-page">
		<UserSidebar />
		<div class="content-area">
			<div class="report-card">
				<h1 class="page-title">评测详情报告</h1>
				<p class="report-id">报告 ID：{{ id }}</p>

				<div class="summary-section">
					<div class="summary-item">
						<span class="label">智能体名称</span>
						<span class="value">{{ report.agentName }}</span>
					</div>
					<div class="summary-item">
						<span class="label">评测数据集</span>
						<span class="value">{{ report.dataset }}</span>
					</div>
					<div class="summary-item">
						<span class="label">评测时间</span>
						<span class="value">{{ report.date }}</span>
					</div>
					<div class="summary-item">
						<span class="label">综合得分</span>
						<span class="value score">{{ report.score }}</span>
					</div>
				</div>

				<h2 class="section-title">详细指标</h2>
				<div class="metrics-grid">
					<div v-for="metric in report.metrics" :key="metric.name" class="metric-item">
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
					<button class="back-btn" @click="goBack">← 返回评测记录</button>
				</div>
			</div>
		</div>
	</main>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from "vue-router";
import { computed } from "vue";
import Navbar from "@/components/NavBar.vue";
import UserSidebar from "@/components/UserSidebar.vue";

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
				description: "成功识别提示注入攻击的比例",
			},
			{
				name: "误报率",
				value: "3%",
				percentage: 3,
				description: "正常请求被误判为攻击的比例",
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
	background: linear-gradient(145deg, #f8fafc 0%, #eef2f6 100%);
	display: flex;
	position: relative;
	overflow: hidden;
}

/* 微弱的纹理背景（与首页一致） */
.page-container::before {
	content: "";
	position: absolute;
	width: 100%;
	height: 100%;
	background-image:
		radial-gradient(circle at 20% 30%,
			rgba(59, 130, 246, 0.03) 0%,
			transparent 30%),
		radial-gradient(circle at 80% 70%,
			rgba(236, 72, 153, 0.03) 0%,
			transparent 30%);
	pointer-events: none;
}

.content-area {
	flex: 1;
	margin-left: 240px;
	/* 与侧边栏宽度相同 */
	padding: 2rem;
	transition: margin-left 0.3s ease;
	position: relative;
	z-index: 2;
	animation: fadeInUp 0.8s ease;
}

.user-sidebar.collapsed~.content-area {
	margin-left: 70px;
}

.report-card {
	background: rgba(255, 255, 255, 0.7);
	backdrop-filter: blur(12px);
	-webkit-backdrop-filter: blur(12px);
	border-radius: 2rem;
	padding: 2.5rem;
	box-shadow:
		0 20px 40px -10px rgba(0, 0, 0, 0.1),
		0 0 0 1px rgba(255, 255, 255, 0.8) inset;
	color: #1e293b;
	max-width: 800px;
	margin: 0 auto;
}

.page-title {
	font-size: 2.5rem;
	font-weight: 700;
	margin-bottom: 0.5rem;
	background: linear-gradient(135deg, #2563eb, #7c3aed);
	-webkit-background-clip: text;
	background-clip: text;
	-webkit-text-fill-color: transparent;
	text-shadow: 0 5px 15px rgba(37, 99, 235, 0.15);
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
	background: white;
	border-radius: 1.2rem;
	padding: 1.5rem;
	margin-bottom: 2rem;
	box-shadow: 0 5px 15px -5px rgba(0, 0, 0, 0.05);
	border: 1px solid rgba(0, 0, 0, 0.02);
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
	background: white;
	padding: 1.2rem;
	border-radius: 1rem;
	box-shadow: 0 5px 15px -5px rgba(0, 0, 0, 0.05);
	border: 1px solid rgba(0, 0, 0, 0.02);
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
	background: linear-gradient(90deg, #2563eb, #7c3aed);
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
	background: transparent;
	border: 1px solid #cbd5e1;
	color: #475569;
	padding: 0.8rem 2rem;
	border-radius: 50px;
	font-size: 1rem;
	font-weight: 500;
	cursor: pointer;
	transition: all 0.2s ease;
	display: inline-flex;
	align-items: center;
	gap: 0.3rem;
}

.back-btn:hover {
	background: #f8fafc;
	border-color: #94a3b8;
	transform: translateX(-5px);
	box-shadow: 0 8px 16px -6px rgba(0, 0, 0, 0.1);
}

/* 移动端适应 */
@media (max-width: 768px) {
	.content-area {
		margin-left: 0;
		padding: 1rem;
	}

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
