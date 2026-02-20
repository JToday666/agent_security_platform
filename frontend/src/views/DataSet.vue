<template>
  <Navbar />
  <main class="page-container dataset-page">
    <div class="content">
      <h1 class="page-title">数据集列表</h1>
      <p class="page-subtitle">选择以下数据集，查看详细说明和下载链接。</p>

      <div class="dataset-grid">
        <router-link
          v-for="item in datasets"
          :key="item.id"
          :to="`/dataset/${item.id}`"
          class="dataset-card"
        >
          <h3>{{ item.name }}</h3>
          <p>{{ item.description }}</p>
          <span class="card-link">查看详情 →</span>
        </router-link>
      </div>
    </div>
  </main>
</template>

<script setup lang="ts">
import Navbar from "@/components/NavBar.vue";

const datasets = [
  {
    id: 1,
    name: "Prompt Injection Dataset",
    description: "包含多种提示注入攻击样本，用于测试智能体对恶意指令的防御能力。",
  },
  {
    id: 2,
    name: "Jailbreak Dataset",
    description: "模拟越狱攻击场景，评估智能体在违规请求下的行为安全性。",
  },
  // 可以继续添加更多数据集
];
</script>

<style scoped>
.page-container {
  min-height: 100vh;
  padding-top: 70px; /* 为固定导航栏留出空间 */
  background: linear-gradient(145deg, #667eea 0%, #764ba2 100%);
  display: flex;
  justify-content: center;
}

.content {
  max-width: 1200px;
  width: 100%;
  padding: 3rem 2rem;
  color: white;
}

.page-title {
  font-size: 2.8rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  text-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.page-subtitle {
  font-size: 1.2rem;
  margin-bottom: 3rem;
  opacity: 0.9;
}

.dataset-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 2rem;
}

.dataset-card {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border-radius: 1.5rem;
  padding: 1.8rem;
  border: 1px solid rgba(255, 255, 255, 0.2);
  transition:
    transform 0.2s,
    box-shadow 0.2s;
  text-decoration: none;
  color: white;
  display: flex;
  flex-direction: column;
}

.dataset-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 20px 30px rgba(0, 0, 0, 0.2);
  background: rgba(255, 255, 255, 0.2);
}

.dataset-card h3 {
  font-size: 1.6rem;
  margin-bottom: 0.8rem;
  font-weight: 600;
}

.dataset-card p {
  font-size: 1rem;
  line-height: 1.6;
  opacity: 0.9;
  margin-bottom: 1.5rem;
  flex: 1;
}

.card-link {
  align-self: flex-end;
  font-weight: 500;
  opacity: 0.9;
  transition: opacity 0.2s;
}

.dataset-card:hover .card-link {
  opacity: 1;
  text-decoration: underline;
}

@media (max-width: 640px) {
  .page-title {
    font-size: 2.2rem;
  }
  .dataset-grid {
    grid-template-columns: 1fr;
  }
}
</style>
