<template>
	<Navbar />
	<main class="page-container detail-page">
		<div class="content">
			<div class="detail-card">
				<div class="card-header">
					<button class="back-btn" @click="goBack">← 返回列表</button>
				</div>

				<div v-if="dataset" class="dataset-info">
					<h1 class="dataset-name">{{ dataset.name }}</h1>
					<p class="dataset-description">{{ dataset.description }}</p>

					<div class="info-grid">
						<div class="info-item">
							<span class="label">样本数量</span>
							<span class="value">{{ dataset.sampleCount }}</span>
						</div>
						<div class="info-item">
							<span class="label">攻击类型</span>
							<span class="value">{{ dataset.attackTypes }}</span>
						</div>
						<div class="info-item">
							<span class="label">数据格式</span>
							<span class="value">{{ dataset.format }}</span>
						</div>
						<div class="info-item">
							<span class="label">发布年份</span>
							<span class="value">{{ dataset.year }}</span>
						</div>
					</div>

					<div class="download-section">
						<a :href="dataset.downloadUrl" class="download-btn" target="_blank" rel="noopener">
							下载数据集
						</a>
					</div>
				</div>

				<div v-else class="not-found">
					<p>数据集不存在或 ID 错误</p>
					<button class="back-btn large" @click="goBack">返回列表</button>
				</div>
			</div>
		</div>
	</main>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from "vue-router";
import { computed } from "vue";
import Navbar from "@/components/NavBar.vue";

// 模拟数据集详情数据（应与 DataSet.vue 中的数据集对应）
const datasets = [
	{
		id: 1,
		name: "Prompt Injection Dataset",
		description:
			"包含多种提示注入攻击样本，用于测试智能体对恶意指令的防御能力。数据集包含 10,000 条精心构造的提示，覆盖常见攻击模式。",
		sampleCount: "10,000",
		attackTypes: "提示注入、指令劫持",
		format: "JSON",
		year: "2024",
		downloadUrl: "#",
	},
	{
		id: 2,
		name: "Jailbreak Dataset",
		description:
			"模拟越狱攻击场景，评估智能体在违规请求下的行为安全性。数据集包含 8,000 条越狱尝试，涵盖多种绕过策略。",
		sampleCount: "8,000",
		attackTypes: "越狱攻击、角色扮演",
		format: "CSV",
		year: "2023",
		downloadUrl: "#",
	},
];

const route = useRoute();
const router = useRouter();

const id = Number(route.params.id);
const dataset = computed(() => datasets.find((d) => d.id === id));

const goBack = () => {
	if (window.history.state?.back) {
		router.back();
	} else {
		router.push("/dataset");
	}
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
		radial-gradient(circle at 20% 30%,
			rgba(59, 130, 246, 0.03) 0%,
			transparent 30%),
		radial-gradient(circle at 80% 70%,
			rgba(236, 72, 153, 0.03) 0%,
			transparent 30%);
	pointer-events: none;
}

.content {
	max-width: 800px;
	width: 100%;
	padding: 2rem;
	position: relative;
	z-index: 2;
	animation: fadeInUp 0.8s ease;
}

.detail-card {
	background: rgba(255, 255, 255, 0.7);
	backdrop-filter: blur(12px);
	-webkit-backdrop-filter: blur(12px);
	border-radius: 2rem;
	padding: 2rem;
	box-shadow:
		0 20px 40px -10px rgba(0, 0, 0, 0.1),
		0 0 0 1px rgba(255, 255, 255, 0.8) inset;
	color: #1e293b;
}

.card-header {
	margin-bottom: 1.5rem;
}

.back-btn {
	background: transparent;
	border: 1px solid #cbd5e1;
	color: #475569;
	padding: 0.5rem 1.2rem;
	border-radius: 30px;
	font-size: 0.95rem;
	cursor: pointer;
	transition: all 0.2s ease;
	display: inline-flex;
	align-items: center;
	gap: 0.3rem;
}

.back-btn:hover {
	background: #f8fafc;
	border-color: #94a3b8;
	transform: translateX(-3px);
	box-shadow: 0 4px 8px rgba(0, 0, 0, 0.02);
}

.dataset-name {
	font-size: 2.5rem;
	font-weight: 700;
	margin-bottom: 1rem;
	color: #0f172a;
}

.dataset-description {
	font-size: 1.1rem;
	line-height: 1.7;
	margin-bottom: 2rem;
	color: #475569;
}

.info-grid {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
	gap: 1.5rem;
	margin-bottom: 2.5rem;
	background: white;
	border-radius: 1.2rem;
	padding: 1.5rem;
	box-shadow: 0 5px 15px -5px rgba(0, 0, 0, 0.05);
	border: 1px solid rgba(0, 0, 0, 0.02);
}

.info-item {
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
	font-size: 1.2rem;
	font-weight: 600;
	color: #0f172a;
}

.download-section {
	text-align: center;
	margin-top: 1rem;
}

.download-btn {
	display: inline-block;
	background: linear-gradient(135deg, #2563eb, #7c3aed);
	color: white;
	padding: 0.9rem 2.5rem;
	border-radius: 50px;
	font-weight: 600;
	text-decoration: none;
	transition:
		transform 0.2s,
		box-shadow 0.2s;
	box-shadow: 0 8px 18px -6px #2563eb80;
	border: none;
}

.download-btn:hover {
	transform: translateY(-3px);
	box-shadow: 0 15px 25px -8px #2563eb;
}

.not-found {
	text-align: center;
	padding: 3rem 0;
}

.not-found p {
	font-size: 1.2rem;
	margin-bottom: 2rem;
	color: #475569;
}

.back-btn.large {
	padding: 0.8rem 2rem;
	font-size: 1rem;
	background: #2563eb;
	color: white;
	border: none;
}

.back-btn.large:hover {
	background: #1d4ed8;
	transform: translateY(-2px);
	box-shadow: 0 10px 20px -8px #2563eb;
}

/* 移动端适应 */
@media (max-width: 640px) {
	.content {
		padding: 1rem;
	}

	.detail-card {
		padding: 1.5rem;
	}

	.dataset-name {
		font-size: 2rem;
	}

	.info-grid {
		grid-template-columns: 1fr 1fr;
		gap: 1rem;
		padding: 1rem;
	}
}
</style>
