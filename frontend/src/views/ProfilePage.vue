<template>
	<Navbar />
	<main class="page-container profile-page">
		<UserSidebar />
		<div class="content-area">
			<div class="form-card">
				<h1 class="page-title">修改信息</h1>
				<p class="page-subtitle">更新您的个人资料和账户信息。</p>

				<form @submit.prevent="handleSubmit" class="profile-form">
					<!-- 头像上传区域 -->
					<div class="avatar-section">
						<div class="avatar-preview">
							<img
								:src="avatarPreview || avatarUrl || defaultAvatar"
								alt="头像"
								v-if="avatarPreview || avatarUrl"
							/>
							<span v-else class="avatar-placeholder">📷</span>
						</div>
						<div class="avatar-upload">
							<label for="avatar" class="upload-label">选择新头像</label>
							<input
								type="file"
								id="avatar"
								accept="image/*"
								@change="onAvatarChange"
								class="hidden-input"
								:disabled="uploading"
							/>
							<p class="hint">支持 JPG、PNG，大小不超过 2MB</p>
							<div v-if="uploading" class="uploading-hint">上传中...</div>
						</div>
					</div>

					<!-- 表单字段 -->
					<div class="form-group">
						<label for="username">用户名</label>
						<input
							type="text"
							id="username"
							v-model="form.username"
							placeholder="请输入用户名"
							required
						/>
					</div>

					<div class="form-group">
						<label for="email">邮箱</label>
						<input
							type="email"
							id="email"
							v-model="form.email"
							readonly
							class="readonly-field"
						/>
						<p class="field-hint">邮箱不可修改</p>
					</div>

					<div class="form-group">
						<label for="password">新密码</label>
						<input
							type="password"
							id="password"
							v-model="form.password"
							placeholder="留空表示不修改"
						/>
					</div>

					<div class="form-group">
						<label for="confirmPassword">确认新密码</label>
						<input
							type="password"
							id="confirmPassword"
							v-model="form.confirmPassword"
							placeholder="再次输入新密码"
						/>
					</div>

					<div v-if="message" class="form-message" :class="messageType">
						{{ message }}
					</div>

					<div class="form-actions">
						<button type="submit" class="submit-btn" :disabled="submitting">
							{{ submitting ? "保存中..." : "保存修改" }}
						</button>
						<button
							type="button"
							class="cancel-btn"
							@click="resetForm"
							:disabled="submitting"
						>
							取消
						</button>
					</div>
				</form>
			</div>
		</div>
	</main>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from "vue";
import { useUserStore } from "@/store/user";
import { storeToRefs } from "pinia";
import Navbar from "@/components/NavBar.vue";
import UserSidebar from "@/components/UserSidebar.vue";

const userStore = useUserStore();
const { currentUser, avatarUrl } = storeToRefs(userStore);

// 默认头像（请替换为实际图片地址）
const defaultAvatar = "https://via.placeholder.com/100?text=Avatar";

// 表单数据
const form = reactive({
	username: "",
	email: "",
	password: "",
	confirmPassword: "",
});

const avatarPreview = ref<string | null>(null);
const submitting = ref(false);
const uploading = ref(false);
const message = ref("");
const messageType = ref<"success" | "error">("success");

// 从 store 加载当前用户信息到表单
const loadUserData = () => {
	if (currentUser.value) {
		form.username = currentUser.value.username || "";
		form.email = currentUser.value.email || ""; // 邮箱只读显示，不用于提交
	}
};

onMounted(() => {
	if (currentUser.value) {
		loadUserData();
	} else {
		userStore
			.fetchProfile()
			.then(() => {
				loadUserData();
			})
			.catch(() => {});
	}
});

watch(currentUser, () => {
	loadUserData();
});

const onAvatarChange = async (e: Event) => {
	const target = e.target as HTMLInputElement;
	const file = target.files?.[0];
	if (!file) return;

	if (file.size > 2 * 1024 * 1024) {
		message.value = "头像大小不能超过 2MB";
		messageType.value = "error";
		target.value = "";
		return;
	}

	const reader = new FileReader();
	reader.onload = (e) => {
		avatarPreview.value = e.target?.result as string;
	};
	reader.readAsDataURL(file);

	uploading.value = true;
	message.value = "";
	try {
		const newUrl = await userStore.uploadAvatar(file);
		avatarPreview.value = null;
		message.value = "头像更新成功";
		messageType.value = "success";
	} catch (error: any) {
		message.value = error.message || "头像上传失败";
		messageType.value = "error";
		avatarPreview.value = null;
	} finally {
		uploading.value = false;
		target.value = "";
	}
};

const handleSubmit = async () => {
	// 密码一致性验证
	if (form.password && form.password !== form.confirmPassword) {
		message.value = "两次输入的密码不一致";
		messageType.value = "error";
		return;
	}

	// 构建更新数据（只包含可修改字段：用户名、密码）
	const updateData: {
		username?: string;
		password?: string;
	} = {};

	if (form.username !== currentUser.value?.username) {
		updateData.username = form.username;
	}
	if (form.password) {
		updateData.password = form.password;
	}

	if (Object.keys(updateData).length === 0) {
		message.value = "没有要保存的修改";
		messageType.value = "error";
		return;
	}

	submitting.value = true;
	message.value = "";

	try {
		await userStore.updateProfile(updateData);
		message.value = "信息更新成功！";
		messageType.value = "success";
		form.password = "";
		form.confirmPassword = "";
	} catch (error: any) {
		message.value = error.message || "更新失败";
		messageType.value = "error";
	} finally {
		submitting.value = false;
	}
};

const resetForm = () => {
	loadUserData(); // 重置为 store 中的原始数据
	form.password = "";
	form.confirmPassword = "";
	avatarPreview.value = null;
	message.value = "";
};
</script>

<style scoped></style>

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

.user-sidebar.collapsed ~ .content-area {
	margin-left: 70px;
}

.form-card {
	background: rgba(255, 255, 255, 0.7);
	backdrop-filter: blur(12px);
	-webkit-backdrop-filter: blur(12px);
	border-radius: 2rem;
	padding: 2.5rem;
	box-shadow:
		0 20px 40px -10px rgba(0, 0, 0, 0.1),
		0 0 0 1px rgba(255, 255, 255, 0.8) inset;
	color: #1e293b;
	max-width: 600px;
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

/* 头像区域 */
.avatar-section {
	display: flex;
	gap: 2rem;
	align-items: center;
	margin-bottom: 2rem;
	background: white;
	padding: 1.5rem;
	border-radius: 1.2rem;
	box-shadow: 0 5px 15px -5px rgba(0, 0, 0, 0.05);
	border: 1px solid rgba(0, 0, 0, 0.02);
}

.avatar-preview {
	width: 80px;
	height: 80px;
	border-radius: 50%;
	background: #f1f5f9;
	display: flex;
	align-items: center;
	justify-content: center;
	overflow: hidden;
	border: 2px solid #fff;
	box-shadow: 0 5px 10px rgba(0, 0, 0, 0.05);
}

.avatar-preview img {
	width: 100%;
	height: 100%;
	object-fit: cover;
}

.avatar-placeholder {
	font-size: 2rem;
	color: #94a3b8;
}

.avatar-upload {
	flex: 1;
}

.upload-label {
	display: inline-block;
	background: linear-gradient(135deg, #2563eb, #7c3aed);
	color: white;
	padding: 0.5rem 1.5rem;
	border-radius: 30px;
	font-weight: 500;
	cursor: pointer;
	transition:
		transform 0.2s,
		box-shadow 0.2s;
	margin-bottom: 0.5rem;
	box-shadow: 0 8px 18px -6px #2563eb80;
	border: none;
	font-size: 0.95rem;
}

.upload-label:hover {
	transform: translateY(-2px);
	box-shadow: 0 15px 25px -8px #2563eb;
}

.hidden-input {
	display: none;
}

.hint {
	font-size: 0.85rem;
	color: #64748b;
	margin: 0;
}

/* 表单组 */
.form-group {
	margin-bottom: 1.5rem;
}

.form-group label {
	display: block;
	margin-bottom: 0.5rem;
	font-weight: 500;
	color: #334155;
}

.form-group input {
	width: 100%;
	padding: 0.8rem 1.2rem;
	background: white;
	border: 1px solid #e2e8f0;
	border-radius: 30px;
	color: #1e293b;
	font-size: 1rem;
	transition:
		border-color 0.2s,
		box-shadow 0.2s;
	box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
}

.form-group input:focus {
	outline: none;
	border-color: #2563eb;
	box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.form-group input::placeholder {
	color: #94a3b8;
}

/* 提示信息 */
.form-message {
	padding: 0.8rem 1.2rem;
	border-radius: 30px;
	margin-bottom: 1.5rem;
	text-align: center;
	font-size: 0.95rem;
}

.form-message.success {
	background: #dcfce7;
	color: #166534;
	border: 1px solid #86efac;
}

.form-message.error {
	background: #fee2e2;
	color: #991b1b;
	border: 1px solid #fca5a5;
}

/* 按钮组 */
.form-actions {
	display: flex;
	gap: 1rem;
	margin-top: 1rem;
}

.submit-btn,
.cancel-btn {
	padding: 0.8rem 2rem;
	border: none;
	border-radius: 50px;
	font-size: 1rem;
	font-weight: 600;
	cursor: pointer;
	transition:
		transform 0.2s,
		box-shadow 0.2s;
	flex: 1;
}

.submit-btn {
	background: linear-gradient(135deg, #2563eb, #7c3aed);
	color: white;
	box-shadow: 0 8px 18px -6px #2563eb80;
}

.submit-btn:hover:not(:disabled) {
	transform: translateY(-2px);
	box-shadow: 0 15px 25px -8px #2563eb;
}

.submit-btn:disabled {
	opacity: 0.6;
	cursor: not-allowed;
	transform: none;
	box-shadow: none;
}

.cancel-btn {
	background: transparent;
	color: #475569;
	border: 1px solid #cbd5e1;
}

.cancel-btn:hover {
	background: #f8fafc;
	border-color: #94a3b8;
	transform: translateY(-2px);
	box-shadow: 0 8px 16px -6px rgba(0, 0, 0, 0.1);
}

/* 响应式 */
@media (max-width: 768px) {
	.content-area {
		margin-left: 0;
		padding: 1rem;
	}

	.form-card {
		padding: 1.5rem;
	}

	.avatar-section {
		flex-direction: column;
		text-align: center;
		gap: 1rem;
	}
}

.hidden-input {
	display: none;
}
.uploading-hint {
	color: #666;
	font-size: 0.85rem;
	margin-top: 0.25rem;
}
.readonly-field {
	background-color: #f5f5f5;
	cursor: not-allowed;
	color: #666;
}
.field-hint {
	font-size: 0.8rem;
	color: #999;
	margin-top: 0.25rem;
}
</style>
