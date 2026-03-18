<template>
	<Teleport to="body">
		<Transition name="fade" @after-leave="afterLeave">
			<div v-if="modelValue" class="confirm-overlay" @click.self="handleCancel">
				<Transition name="scale" appear>
					<div class="confirm-card">
						<!-- 可选图标 -->
						<div class="icon-wrapper" v-if="showIcon">
							<ExclamationTriangleIcon class="icon" />
						</div>

						<!-- 标题与内容 -->
						<h3 v-if="title" class="confirm-title">{{ title }}</h3>
						<p class="confirm-message">{{ message }}</p>

						<!-- 按钮组 -->
						<div class="button-group" :class="{ single: !showCancel }">
							<button v-if="showCancel" class="btn cancel" @click="handleCancel" :disabled="loading">
								{{ cancelText }}
							</button>
							<button class="btn confirm" :class="{ danger }" @click="handleConfirm" :disabled="loading">
								<span v-if="!loading">{{ confirmText }}</span>
								<span v-else class="loader"></span>
							</button>
						</div>
					</div>
				</Transition>
			</div>
		</Transition>
	</Teleport>
</template>

<script setup lang="ts">
import { ExclamationTriangleIcon } from "@heroicons/vue/24/outline";

interface Props {
	modelValue: boolean; // 控制显示
	title?: string; // 标题（可选）
	message: string; // 提示内容
	confirmText?: string; // 确认按钮文字（默认“确认”）
	cancelText?: string; // 取消按钮文字（默认“取消”）
	showCancel?: boolean; // 是否显示取消按钮（默认 true）
	danger?: boolean; // 是否为危险操作（红色确认按钮）
	showIcon?: boolean; // 是否显示感叹号图标（默认 true）
	loading?: boolean; // 外部控制加载状态
}

const props = withDefaults(defineProps<Props>(), {
	title: "提示",
	confirmText: "确认",
	cancelText: "取消",
	showCancel: true,
	danger: false,
	showIcon: true,
	loading: false,
});

const emit = defineEmits<{
	(e: "update:modelValue", value: boolean): void;
	(e: "confirm"): void;
	(e: "cancel"): void;
}>();

// 关闭弹窗（不触发确认）
const close = () => {
	emit("update:modelValue", false);
};

// 点击取消
const handleCancel = () => {
	if (props.loading) return;
	emit("cancel");
	close();
};

// 点击确认
const handleConfirm = () => {
	if (props.loading) return;
	emit("confirm");
	// 注意：外部通常会在异步操作完成后手动关闭，所以这里不自动关闭
	// 如果不需要异步，可以 close()，但为了通用性，交由外部控制
};

// 动画结束后额外清理（如果有需要）
const afterLeave = () => {
	// 可在此重置内部状态
};
</script>

<style scoped>
/* 遮罩层 */
.confirm-overlay {
	position: fixed;
	top: 0;
	left: 0;
	width: 100%;
	height: 100%;
	background-color: rgba(0, 0, 0, 0.4);
	backdrop-filter: blur(4px);
	display: flex;
	align-items: center;
	justify-content: center;
	z-index: 2000;
}

/* 卡片 */
.confirm-card {
	background: rgba(255, 255, 255, 0.9);
	backdrop-filter: blur(16px);
	-webkit-backdrop-filter: blur(16px);
	border-radius: 32px;
	padding: 2rem 2rem 1.8rem;
	width: 90%;
	max-width: 380px;
	box-shadow:
		0 30px 60px -15px rgba(0, 0, 0, 0.3),
		0 0 0 1px rgba(255, 255, 255, 0.7) inset;
	text-align: center;
	color: #1e293b;
}

/* 图标 */
.icon-wrapper {
	display: flex;
	justify-content: center;
	margin-bottom: 1.2rem;
}

.icon {
	width: 48px;
	height: 48px;
	color: #f59e0b;
	/* 警告色 */
	filter: drop-shadow(0 4px 6px rgba(245, 158, 11, 0.2));
}

/* 标题 */
.confirm-title {
	font-size: 1.6rem;
	font-weight: 600;
	margin: 0 0 0.5rem;
	color: #0f172a;
}

/* 内容 */
.confirm-message {
	font-size: 1rem;
	color: #475569;
	margin: 0 0 2rem;
	line-height: 1.5;
	white-space: pre-line;
	/* 支持换行 */
}

/* 按钮组 */
.button-group {
	display: flex;
	gap: 12px;
	justify-content: center;
}

.button-group.single {
	grid-template-columns: 1fr;
}

.btn {
	flex: 1;
	padding: 0.8rem 1.2rem;
	border: none;
	border-radius: 40px;
	font-size: 1rem;
	font-weight: 600;
	cursor: pointer;
	transition: all 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275);
	box-shadow: 0 4px 8px rgba(0, 0, 0, 0.02);
	display: inline-flex;
	align-items: center;
	justify-content: center;
	gap: 8px;
}

.btn:disabled {
	opacity: 0.6;
	cursor: not-allowed;
	transform: none;
	box-shadow: none;
}

/* 取消按钮 */
.cancel {
	background: white;
	color: #64748b;
	border: 1px solid #e2e8f0;
}

.cancel:hover:not(:disabled) {
	background: #f8fafc;
	border-color: #cbd5e1;
	transform: translateY(-2px);
	box-shadow: 0 10px 20px -8px rgba(0, 0, 0, 0.1);
}

/* 确认按钮（普通） */
.confirm {
	background: linear-gradient(135deg, #2563eb, #7c3aed);
	color: white;
	box-shadow: 0 8px 18px -6px #2563eb80;
}

.confirm:hover:not(:disabled) {
	background: linear-gradient(135deg, #1d4ed8, #6d28d9);
	transform: translateY(-2px);
	box-shadow: 0 15px 25px -8px #2563eb;
}

/* 危险确认按钮（红色） */
.confirm.danger {
	background: linear-gradient(135deg, #f87171, #ef4444);
	box-shadow: 0 8px 18px -6px #ef444480;
}

.confirm.danger:hover:not(:disabled) {
	background: linear-gradient(135deg, #ef4444, #dc2626);
	box-shadow: 0 15px 25px -8px #ef4444;
}

/* 加载动画 */
.loader {
	display: inline-block;
	width: 20px;
	height: 20px;
	border: 2px solid rgba(255, 255, 255, 0.3);
	border-radius: 50%;
	border-top-color: white;
	animation: spin 0.8s linear infinite;
}

@keyframes spin {
	to {
		transform: rotate(360deg);
	}
}

/* 过渡动画 */
.fade-enter-active,
.fade-leave-active {
	transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
	opacity: 0;
}

.scale-enter-active {
	transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.scale-enter-from {
	transform: scale(0.9);
}
</style>
