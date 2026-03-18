<template>
	<Navbar />
	<main class="page-container user-center">
		<!-- 左侧侧边栏 -->
		<UserSidebar />
		<div class="content-area">
			<div class="records-card">
				<h1 class="page-title">评测记录</h1>
				<p class="page-subtitle">您提交过的所有智能体评测历史。</p>

				<div class="records-list">
					<div v-for="record in records" :key="record.id" class="record-item">
						<div class="record-info">
							<h3>{{ record.name }}</h3>
							<p>数据集：{{ record.dataset }} · 提交时间：{{ record.date }}</p>
						</div>
						<router-link :to="`/report/${record.id}`" class="view-btn">
							查看报告 →
						</router-link>
					</div>
				</div>

				<div v-if="records.length === 0" class="empty-state">
					<p>您还没有提交过智能体评测。</p>
					<router-link to="/submit" class="btn">立即提交</router-link>
				</div>
			</div>
		</div>
	</main>
</template>

<script setup lang="ts">
import Navbar from "@/components/NavBar.vue";
import UserSidebar from "@/components/UserSidebar.vue";

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

/* 微弱的纹理背景 */
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

/* 当侧边栏收起时，调整左边距（需配合 UserSidebar 组件） */
.user-sidebar.collapsed~.content-area {
	margin-left: 70px;
}

.records-card {
	background: rgba(255, 255, 255, 0.7);
	backdrop-filter: blur(12px);
	-webkit-backdrop-filter: blur(12px);
	border-radius: 2rem;
	padding: 2rem 2.5rem;
	box-shadow:
		0 20px 40px -10px rgba(0, 0, 0, 0.1),
		0 0 0 1px rgba(255, 255, 255, 0.8) inset;
	color: #1e293b;
	max-width: 900px;
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

.page-subtitle {
	font-size: 1.1rem;
	color: #475569;
	margin-bottom: 2rem;
	line-height: 1.6;
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
	background: white;
	padding: 1.2rem 1.5rem;
	border-radius: 1.2rem;
	border: 1px solid rgba(0, 0, 0, 0.02);
	transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
	box-shadow: 0 5px 15px -5px rgba(0, 0, 0, 0.05);
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
	background: linear-gradient(135deg, #2563eb, #7c3aed);
	color: white;
	padding: 0.5rem 1.2rem;
	border-radius: 30px;
	text-decoration: none;
	font-weight: 500;
	transition:
		transform 0.2s,
		box-shadow 0.2s;
	box-shadow: 0 8px 18px -6px #2563eb80;
	display: inline-flex;
	align-items: center;
	gap: 0.3rem;
}

.view-btn:hover {
	transform: translateY(-2px);
	box-shadow: 0 15px 25px -8px #2563eb;
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
	background: linear-gradient(135deg, #2563eb, #7c3aed);
	color: white;
	padding: 0.8rem 2rem;
	border-radius: 50px;
	text-decoration: none;
	font-weight: 600;
	transition:
		transform 0.2s,
		box-shadow 0.2s;
	box-shadow: 0 8px 18px -6px #2563eb80;
}

.btn:hover {
	transform: translateY(-2px);
	box-shadow: 0 15px 25px -8px #2563eb;
}

@media (max-width: 768px) {
	.content-area {
		margin-left: 0;
		padding: 1rem;
	}

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
