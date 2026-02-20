<template>
  <Navbar />
  <main class="home-main">
    <div class="hero">
      <h1 class="title">智能体安全评测平台</h1>
      <p class="subtitle">安全、可靠、专业的智能体评估系统 —— 让每一次评测都有据可依。</p>

      <!-- 使用说明卡片 -->
      <div class="guide">
        <h2>如何使用本平台？</h2>
        <div class="steps">
          <div class="step">
            <div class="step-number">1</div>
            <h3>注册/登录</h3>
            <p>创建账号或登录，开启您的智能体评测之旅。</p>
          </div>
          <div class="step">
            <div class="step-number">2</div>
            <h3>提交智能体</h3>
            <p>在个人中心提交您的智能体，选择测试数据集。</p>
          </div>
          <div class="step">
            <div class="step-number">3</div>
            <h3>查看评测报告</h3>
            <p>获取详细的评测结果，优化您的智能体。</p>
          </div>
          <div class="step">
            <div class="step-number">4</div>
            <h3>登上排行榜</h3>
            <p>公开您的智能体，与其他开发者一较高下。</p>
          </div>
        </div>
      </div>

      <!-- 操作按钮组 -->
      <div class="action-buttons">
        <button class="btn primary" @click="goDataset">浏览数据集</button>
        <button class="btn secondary" @click="goLeaderboard">查看排行榜</button>
        <!-- 登录/注册按钮（未登录时显示） -->
        <button v-if="!isLogin" class="btn accent" @click="openLoginDialog">登录 / 注册</button>
        <!-- 已登录时显示欢迎语和进入个人中心按钮 -->
        <div v-else class="user-greeting">
          欢迎回来，<strong>{{ username }}</strong> ！
          <router-link to="/user" class="btn outline">进入个人中心</router-link>
        </div>
      </div>
    </div>
  </main>

  <!-- 登录对话框组件 -->
  <LoginDialog />
</template>

<script setup lang="ts">
import { useRouter } from "vue-router";
import { useUserStore } from "@/store/user";
import { storeToRefs } from "pinia";
import Navbar from "@/components/NavBar.vue";
import LoginDialog from "@/components/LoginDialog.vue";

const router = useRouter();
const userStore = useUserStore();
const { isLogin, username } = storeToRefs(userStore);

const goDataset = () => router.push("/dataset");
const goLeaderboard = () => router.push("/leaderboard");

const openLoginDialog = () => {
  userStore.openLoginDialog();
};
</script>

<style scoped>
/* 主体区域：顶部留出导航栏高度，背景渐变 */
.home-main {
  min-height: 100vh;
  padding-top: 70px; /* 与导航栏高度一致 */
  background: linear-gradient(145deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}

.hero {
  max-width: 1000px;
  margin: 0 auto;
  padding: 3rem 2rem;
  text-align: center;
  color: white;
}

.title {
  font-size: 3.2rem;
  font-weight: 800;
  margin-bottom: 1rem;
  letter-spacing: -1px;
  text-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  line-height: 1.2;
}

.subtitle {
  font-size: 1.3rem;
  margin-bottom: 3rem;
  opacity: 0.95;
  max-width: 700px;
  margin-left: auto;
  margin-right: auto;
}

/* 使用说明卡片区 */
.guide {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border-radius: 2rem;
  padding: 2.5rem 2rem;
  margin: 3rem 0;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.guide h2 {
  font-size: 2rem;
  margin-bottom: 2rem;
  font-weight: 600;
}

.steps {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 2rem;
}

.step {
  text-align: center;
}

.step-number {
  width: 50px;
  height: 50px;
  background: white;
  color: #667eea;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0 auto 1rem;
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
}

.step h3 {
  font-size: 1.3rem;
  margin-bottom: 0.5rem;
  font-weight: 600;
}

.step p {
  font-size: 0.95rem;
  opacity: 0.9;
  line-height: 1.5;
}

/* 按钮组 */
.action-buttons {
  display: flex;
  gap: 1.2rem;
  justify-content: center;
  align-items: center;
  flex-wrap: wrap;
  margin-top: 2rem;
}

.btn {
  padding: 0.9rem 2.2rem;
  border: none;
  border-radius: 50px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition:
    transform 0.2s,
    box-shadow 0.2s,
    background 0.2s;
  text-decoration: none;
  display: inline-block;
}

.btn:hover {
  transform: translateY(-3px);
  box-shadow: 0 15px 25px rgba(0, 0, 0, 0.15);
}

.primary {
  background: white;
  color: #667eea;
}

.primary:hover {
  background: #f8fafc;
}

.secondary {
  background: transparent;
  color: white;
  border: 2px solid white;
}

.secondary:hover {
  background: rgba(255, 255, 255, 0.1);
}

.accent {
  background: #fbbf24;
  color: #1e293b;
}

.accent:hover {
  background: #f59e0b;
}

.outline {
  background: transparent;
  color: white;
  border: 2px solid white;
  padding: 0.6rem 1.8rem;
  margin-left: 0.5rem;
}

.user-greeting {
  display: flex;
  align-items: center;
  gap: 1rem;
  background: rgba(255, 255, 255, 0.2);
  padding: 0.7rem 1.8rem;
  border-radius: 50px;
  backdrop-filter: blur(5px);
  font-size: 1.1rem;
}

.user-greeting strong {
  font-weight: 700;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .title {
    font-size: 2.5rem;
  }
  .subtitle {
    font-size: 1.1rem;
  }
  .steps {
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }
  .guide h2 {
    font-size: 1.6rem;
  }
}
</style>
