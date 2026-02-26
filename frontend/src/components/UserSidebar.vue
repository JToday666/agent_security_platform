<template>
	<aside class="user-sidebar" :class="{ collapsed }">
		<!-- 收起/展开按钮，放在右上角 -->
		<button class="toggle-btn" @click="collapsed = !collapsed">
			<span v-if="collapsed">▶</span>
			<span v-else>◀</span>
		</button>

		<!-- 导航链接 -->
		<nav class="sidebar-nav">
			<router-link to="/user" class="nav-item" active-class="active">
				<span class="icon">📋</span>
				<span class="text" v-if="!collapsed">评测记录</span>
			</router-link>
			<router-link to="/submit" class="nav-item" active-class="active">
				<span class="icon">🤖</span>
				<span class="text" v-if="!collapsed">提交智能体</span>
			</router-link>
			<router-link to="/profile" class="nav-item" active-class="active">
				<span class="icon">✏️</span>
				<span class="text" v-if="!collapsed">修改信息</span>
			</router-link>
			<router-link to="/dataset" class="nav-item" active-class="active">
				<span class="icon">📊</span>
				<span class="text" v-if="!collapsed">数据集</span>
			</router-link>
			<router-link to="/leaderboard" class="nav-item" active-class="active">
				<span class="icon">🏆</span>
				<span class="text" v-if="!collapsed">排行榜</span>
			</router-link>
			<router-link to="/contact" class="nav-item" active-class="active">
				<span class="icon">📧</span>
				<span class="text" v-if="!collapsed">联系我们</span>
			</router-link>
		</nav>
	</aside>
</template>

<script setup lang="ts">
import { ref } from "vue";

const collapsed = ref(false);
</script>

<style scoped>
.user-sidebar {
	position: fixed;
	left: 0;
	top: 70px;
	/* 与导航栏高度一致 */
	height: calc(100vh - 70px);
	background: rgba(255, 255, 255, 0.7);
	backdrop-filter: blur(12px);
	-webkit-backdrop-filter: blur(12px);
	border-right: 1px solid rgba(0, 0, 0, 0.05);
	box-shadow: 5px 0 20px rgba(0, 0, 0, 0.03);
	transition: width 0.3s ease;
	width: 240px;
	z-index: 900;
	display: flex;
	flex-direction: column;
}

.user-sidebar.collapsed {
	width: 70px;
}

.toggle-btn {
	align-self: flex-end;
	background: rgba(0, 0, 0, 0.03);
	border: 1px solid rgba(0, 0, 0, 0.08);
	color: #64748b;
	width: 30px;
	height: 30px;
	border-radius: 50%;
	margin: 1rem 1rem 0.5rem;
	cursor: pointer;
	display: flex;
	align-items: center;
	justify-content: center;
	transition:
		background 0.2s,
		color 0.2s;
	font-size: 1rem;
}

.toggle-btn:hover {
	background: rgba(0, 0, 0, 0.06);
	color: #2563eb;
}

.sidebar-nav {
	display: flex;
	flex-direction: column;
	padding: 0.5rem 0;
}

.nav-item {
	display: flex;
	align-items: center;
	gap: 1rem;
	padding: 0.8rem 1.5rem;
	color: #334155;
	text-decoration: none;
	transition:
		background 0.2s,
		color 0.2s;
	white-space: nowrap;
	overflow: hidden;
	border-left: 4px solid transparent;
}

.nav-item:hover {
	background: rgba(0, 0, 0, 0.02);
	color: #2563eb;
}

.nav-item.active {
	background: rgba(59, 130, 246, 0.05);
	border-left: 4px solid #2563eb;
	color: #2563eb;
	font-weight: 500;
}

.icon {
	font-size: 1.4rem;
	min-width: 24px;
	text-align: center;
}

.text {
	font-size: 1rem;
	font-weight: 500;
	opacity: 0.9;
}

/* 收起时隐藏文字，图标居中 */
.user-sidebar.collapsed .nav-item {
	justify-content: center;
	padding: 0.8rem 0;
}

.user-sidebar.collapsed .icon {
	margin: 0;
}

.user-sidebar.collapsed .text {
	display: none;
}

/* 响应式 */
@media (max-width: 768px) {
	.user-sidebar {
		width: 200px;
	}

	.user-sidebar.collapsed {
		width: 60px;
	}
}
</style>
