<template>
    <Navbar />
    <main class="home-main">
        <div class="hero">
            <!-- 标题区域 -->
            <div class="hero-content">
                <h1 class="title">智能体安全评测平台</h1>
                <p class="subtitle">安全 · 可靠 · 专业的智能体评估系统</p>
                <p class="description">让每一次评测都有据可依，助您打造更安全的智能体</p>
            </div>

            <!-- 使用指南卡片 -->
            <div class="guide-card">
                <h2 class="guide-title">三步快速上手</h2>
                <div class="steps-grid">
                    <div class="step-item" v-for="(step, index) in steps" :key="index">
                        <div class="step-number">{{ index + 1 }}</div>
                        <h3>{{ step.title }}</h3>
                        <p>{{ step.desc }}</p>
                    </div>
                </div>
            </div>

            <!-- 操作按钮区域（分两行） -->
            <div class="actions">
                <!-- 第一行：核心功能按钮 -->
                <div class="primary-actions">
                    <button class="btn primary" @click="goDataset">
                        <span>📊</span> 浏览数据集
                    </button>
                    <button class="btn primary" @click="goLeaderboard">
                        <span>🏆</span> 查看排行榜
                    </button>
                </div>

                <!-- 第二行：用户相关（登录/个人中心） -->
                <div class="user-actions">
                    <template v-if="!isLogin">
                        <button class="btn accent" @click="openLoginDialog">
                            <span>✨</span> 登录 / 注册
                        </button>
                    </template>
                    <template v-else>
                        <div class="welcome-card">
                            <span class="greeting">欢迎回来，<strong>{{ username }}</strong>！</span>
                            <div class="action-buttons">
                                <router-link to="/user" class="btn outline">
                                    <span>👤</span> 个人中心
                                </router-link>
                                <button class="btn logout" @click="handleLogoutClick">
                                    <span>🚪</span> 退出
                                </button>
                            </div>
                        </div>
                    </template>
                </div>
            </div>
        </div>
    </main>

    <!-- 登录弹窗 -->
    <LoginDialog />

    <!-- 退出确认弹窗 -->
    <ConfirmDialog v-model="showLogoutConfirm" title="确认退出" message="您确定要退出登录吗？" confirm-text="退出" cancel-text="取消"
        :danger="true" :loading="logoutLoading" @confirm="handleLogoutConfirm" @cancel="handleLogoutCancel" />
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useUserStore } from "@/store/user";
import { storeToRefs } from "pinia";
import Navbar from "@/components/NavBar.vue";
import LoginDialog from "@/components/LoginDialog.vue";
import ConfirmDialog from "@/components/ConfirmDialog.vue";

const router = useRouter();
const userStore = useUserStore();
const { isLogin, username } = storeToRefs(userStore);

// 步骤数据
const steps = [
    { title: "注册/登录", desc: "创建账号或登录，开启评测之旅" },
    { title: "提交智能体", desc: "在个人中心上传您的智能体，选择测试数据集" },
    { title: "查看报告", desc: "获取详细评测结果，优化智能体性能" },
    { title: "登上榜单", desc: "公开您的智能体，与其他开发者一较高下" },
];

// 页面跳转
const goDataset = () => router.push("/dataset");
const goLeaderboard = () => router.push("/leaderboard");
const openLoginDialog = () => userStore.openLoginDialog();

// 退出确认逻辑
const showLogoutConfirm = ref(false);
const logoutLoading = ref(false);

const handleLogoutClick = () => {
    showLogoutConfirm.value = true;
};

const handleLogoutConfirm = () => {
    logoutLoading.value = true;
    // 模拟异步操作（实际可调用 userStore.logout()）
    setTimeout(() => {
        userStore.logout();
        router.push("/");
        showLogoutConfirm.value = false;
        logoutLoading.value = false;
    }, 100);
};

const handleLogoutCancel = () => {
    showLogoutConfirm.value = false;
};
</script>

<style scoped>
/* 全局重置与动画 */
* {
    box-sizing: border-box;
}

@keyframes float {

    0%,
    100% {
        transform: translateY(0);
    }

    50% {
        transform: translateY(-5px);
    }
}

.home-main {
    min-height: 100vh;
    padding-top: 80px;
    background: linear-gradient(145deg, #f8fafc 0%, #eef2f6 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    overflow: hidden;
}

/* 浅色背景上的微弱纹理 */
.home-main::before {
    content: '';
    position: absolute;
    width: 100%;
    height: 100%;
    background-image: radial-gradient(circle at 20% 30%, rgba(59, 130, 246, 0.03) 0%, transparent 30%),
        radial-gradient(circle at 80% 70%, rgba(236, 72, 153, 0.03) 0%, transparent 30%);
    pointer-events: none;
}

.hero {
    max-width: 1200px;
    width: 100%;
    margin: 0 auto;
    padding: 2rem 2rem 3rem;
    color: #1e293b;
    position: relative;
    z-index: 2;
}

.hero-content {
    text-align: center;
    margin-bottom: 3rem;
    animation: fadeInUp 1s ease;
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

.title {
    font-size: 3.5rem;
    font-weight: 800;
    margin-bottom: 0.5rem;
    background: linear-gradient(135deg, #2563eb, #7c3aed);
    -webkit-background-clip: text;
    background-clip: text;
    /* 添加标准属性，消除警告 */
    -webkit-text-fill-color: transparent;
    text-shadow: 0 5px 15px rgba(37, 99, 235, 0.15);
}

.subtitle {
    font-size: 1.5rem;
    font-weight: 500;
    margin-bottom: 0.5rem;
    letter-spacing: 1px;
    color: #475569;
}

.description {
    font-size: 1.1rem;
    color: #64748b;
    max-width: 600px;
    margin: 0 auto;
}

/* 指南卡片 */
.guide-card {
    background: rgba(255, 255, 255, 0.7);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-radius: 3rem;
    padding: 2.5rem;
    margin: 3rem 0;
    box-shadow: 0 20px 40px -10px rgba(0, 0, 0, 0.1),
        0 0 0 1px rgba(255, 255, 255, 0.8) inset;
    transition: transform 0.3s ease;
}

.guide-card:hover {
    transform: scale(1.01);
}

.guide-title {
    text-align: center;
    font-size: 2rem;
    margin-bottom: 2rem;
    font-weight: 600;
    color: #0f172a;
}

.steps-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 2rem;
}

.step-item {
    background: white;
    border-radius: 1.5rem;
    padding: 1.5rem 1rem;
    text-align: center;
    transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
    cursor: default;
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05);
}

.step-item:hover {
    transform: translateY(-5px);
    box-shadow: 0 20px 35px -8px rgba(0, 0, 0, 0.15);
}

.step-number {
    width: 60px;
    height: 60px;
    background: linear-gradient(135deg, #2563eb, #7c3aed);
    color: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.8rem;
    font-weight: 700;
    margin: 0 auto 1rem;
    box-shadow: 0 8px 16px -4px rgba(37, 99, 235, 0.3);
}

.step-item h3 {
    font-size: 1.3rem;
    margin-bottom: 0.5rem;
    color: #0f172a;
}

.step-item p {
    font-size: 0.9rem;
    color: #64748b;
    line-height: 1.5;
}

/* 操作区域 */
.actions {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
    align-items: center;
    margin-top: 2rem;
}

.primary-actions {
    display: flex;
    gap: 1.2rem;
    flex-wrap: wrap;
    justify-content: center;
}

.user-actions {
    display: flex;
    justify-content: center;
    width: 100%;
}

.welcome-card {
    display: flex;
    align-items: center;
    gap: 1.5rem;
    background: white;
    backdrop-filter: blur(5px);
    padding: 0.8rem 2rem;
    border-radius: 50px;
    box-shadow: 0 5px 20px rgba(0, 0, 0, 0.05);
    border: 1px solid rgba(0, 0, 0, 0.05);
}

.greeting {
    font-size: 1.1rem;
    color: #334155;
}

.greeting strong {
    color: #2563eb;
    font-weight: 600;
}

.action-buttons {
    display: flex;
    gap: 0.8rem;
}

/* 按钮样式 */
.btn {
    display: inline-flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.9rem 2.2rem;
    border: none;
    border-radius: 50px;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    text-decoration: none;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.02);
}

.btn span {
    font-size: 1.2rem;
}

.btn:hover {
    transform: translateY(-2px) scale(1.02);
    box-shadow: 0 12px 24px -8px rgba(0, 0, 0, 0.15);
}

.btn:active {
    transform: translateY(0);
}

.primary {
    background: white;
    color: #1e293b;
    border: 1px solid #e2e8f0;
}

.primary:hover {
    background: #f8fafc;
    border-color: #cbd5e1;
}

.accent {
    background: linear-gradient(135deg, #2563eb, #7c3aed);
    color: white;
    border: none;
    box-shadow: 0 8px 18px -6px #2563eb80;
}

.accent:hover {
    background: linear-gradient(135deg, #1d4ed8, #6d28d9);
}

.outline {
    background: transparent;
    color: #2563eb;
    border: 2px solid #2563eb30;
    padding: 0.6rem 1.5rem;
}

.outline:hover {
    background: #2563eb0c;
    border-color: #2563eb;
}

.logout {
    background: transparent;
    color: #ef4444;
    border: 2px solid #ef444430;
    padding: 0.6rem 1.5rem;
}

.logout:hover {
    background: #ef44440c;
    border-color: #ef4444;
}

/* 响应式调整 */
@media (max-width: 768px) {
    .title {
        font-size: 2.5rem;
    }

    .subtitle {
        font-size: 1.2rem;
    }

    .steps-grid {
        grid-template-columns: 1fr;
    }

    .primary-actions {
        flex-direction: column;
        width: 100%;
    }

    .primary-actions .btn {
        width: 100%;
        justify-content: center;
    }

    .welcome-card {
        flex-direction: column;
        gap: 1rem;
        padding: 1.2rem;
        border-radius: 30px;
    }

    .action-buttons {
        flex-direction: column;
        width: 100%;
    }

    .action-buttons .btn {
        width: 100%;
        justify-content: center;
    }
}
</style>