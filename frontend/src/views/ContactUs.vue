<template>
	<div class="contact-page">
		<div class="content">
			<div class="contact-card ui-surface-glass">
				<h1 class="page-title">联系我们</h1>
				<p class="page-subtitle">
					如果您有任何问题或建议，欢迎通过以下方式与我们取得联系。
				</p>

				<div class="contact-grid">
					<div v-for="item in contactItems" :key="item.title" class="contact-item ui-surface-white">
						<span class="icon">{{ item.icon }}</span>
						<div class="info">
							<h3>{{ item.title }}</h3>

							<!-- 邮箱/电话 (link 类型) -->
							<template v-if="item.type === 'link'">
								<a :href="item.link">{{ item.text }}</a>
							</template>

							<!-- 地址 (text 类型) -->
							<template v-else-if="item.type === 'text'">
								<p>{{ item.text }}</p>
							</template>

							<!-- 社交媒体 (social 类型) -->
							<template v-else-if="item.type === 'social'">
								<div class="social-links">
									<a v-for="social in item.links" :key="social.name" :href="social.url"
										target="_blank">{{ social.name }}</a>
									<span v-if="item.links.length > 1" class="separator">·</span>
								</div>
							</template>
						</div>
					</div>
				</div>

				<div class="note">
					<p>我们会在 24 小时内回复您的邮件，感谢您的支持！</p>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
type ContactItem =
	| {
		icon: string;
		title: string;
		type: "link";
		text: string;
		link: string;
	}
	| {
		icon: string;
		title: string;
		type: "text";
		text: string;
	}
	| {
		icon: string;
		title: string;
		type: "social";
		links: { name: string; url: string }[];
	};

const contactItems: ContactItem[] = [
	{
		icon: "📧",
		title: "邮箱",
		type: "link",
		text: "u202312421@hust.edu.com",
		link: "mailto:u202312421@hust.edu.com",
	},
	{
		icon: "📞",
		title: "电话",
		type: "link",
		text: "+86 13886038599",
		link: "tel:+8613886038599",
	},
	{
		icon: "📍",
		title: "地址",
		type: "text",
		text: "武汉市东西湖区国家网络安全基地",
	},
	{
		icon: "🌐",
		title: "社交媒体",
		type: "social",
		links: [
			{ name: "Twitter", url: "#" },
			{ name: "GitHub", url: "#" },
		],
	},
];
</script>

<style scoped>
/* 全局重置与动画 */
.contact-page {
	min-height: calc(100vh - 80px);
	display: flex;
	align-items: center;
	justify-content: center;
}

.content {
	max-width: 800px;
	padding: 2rem;
}

.contact-card {
	border-radius: 3rem;
	padding: 3rem 2.5rem;
}

.page-title {
	font-size: 3rem;
	font-weight: 800;
	margin-bottom: 0.5rem;
	text-align: center;
}

.page-subtitle {
	font-size: 1.1rem;
	margin-bottom: 2.5rem;
	text-align: center;
}

.contact-grid {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
	gap: 1.5rem;
	margin: 2rem 0;
}

.contact-item {
	display: flex;
	align-items: flex-start;
	gap: 1rem;
	padding: 1.5rem;
}

.icon {
	font-size: 2.2rem;
	line-height: 1;
	filter: drop-shadow(0 4px 6px rgba(0, 0, 0, 0.05));
}

.info {
	flex: 1;
}

.info h3 {
	font-size: 1.3rem;
	font-weight: 600;
	margin-bottom: 0.3rem;
	color: #0f172a;
}

.info a,
.info p {
	color: #64748b;
	text-decoration: none;
	font-size: 0.95rem;
	line-height: 1.5;
	word-break: break-word;
	transition: color 0.2s;
}

.info a:hover {
	color: #2563eb;
	text-decoration: underline;
}

.social-links {
	display: flex;
	gap: 0.5rem;
	flex-wrap: wrap;
	align-items: center;
}

.social-links a {
	color: #64748b;
}

.social-links a:hover {
	color: #2563eb;
}

.separator {
	color: #cbd5e1;
	margin: 0 0.2rem;
}

.note {
	text-align: center;
	margin-top: 2rem;
	padding-top: 1.5rem;
	border-top: 1px solid #e2e8f0;
	color: #64748b;
	font-style: italic;
}

/* 移动端适应 */
@media (max-width: 640px) {
	.content {
		padding: 1rem;
	}

	.contact-card {
		padding: 2rem 1.5rem;
		border-radius: 2rem;
	}

	.page-title {
		font-size: 2.5rem;
	}

	.contact-grid {
		grid-template-columns: 1fr;
	}

	.contact-item {
		padding: 1.2rem;
	}
}
</style>
