<template>
  <Navbar />
  <main class="page-container detail-page">
    <div class="content">
      <!-- 返回按钮（置于卡片外也可，但放在卡片内更整体） -->
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
    downloadUrl: "#", // 实际应为真实下载链接
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

// 从路由参数获取 id，并转换为数字
const id = Number(route.params.id);

// 根据 id 查找对应数据集
const dataset = computed(() => datasets.find((d) => d.id === id));

// 返回上一页或数据集列表
const goBack = () => {
  // 如果有历史记录则返回，否则跳转到数据集列表
  if (window.history.state?.back) {
    router.back();
  } else {
    router.push("/dataset");
  }
};
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
  max-width: 800px;
  width: 100%;
  padding: 2rem;
}

.detail-card {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border-radius: 2rem;
  border: 1px solid rgba(255, 255, 255, 0.2);
  padding: 2rem;
  color: white;
  box-shadow: 0 20px 35px -8px rgba(0, 0, 0, 0.2);
}

.card-header {
  margin-bottom: 1.5rem;
}

.back-btn {
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
  padding: 0.5rem 1.2rem;
  border-radius: 30px;
  font-size: 0.95rem;
  cursor: pointer;
  transition:
    background 0.2s,
    transform 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
}

.back-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateX(-3px);
}

.dataset-name {
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 1rem;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.dataset-description {
  font-size: 1.1rem;
  line-height: 1.7;
  margin-bottom: 2rem;
  opacity: 0.9;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2.5rem;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 1.2rem;
  padding: 1.5rem;
  border: 1px solid rgba(255, 255, 255, 0.15);
}

.info-item {
  display: flex;
  flex-direction: column;
}

.label {
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  opacity: 0.7;
  margin-bottom: 0.3rem;
}

.value {
  font-size: 1.2rem;
  font-weight: 600;
}

.download-section {
  text-align: center;
  margin-top: 1rem;
}

.download-btn {
  display: inline-block;
  background: white;
  color: #667eea;
  padding: 0.9rem 2.5rem;
  border-radius: 50px;
  font-weight: 600;
  text-decoration: none;
  transition:
    transform 0.2s,
    box-shadow 0.2s;
  box-shadow: 0 10px 15px -5px rgba(0, 0, 0, 0.2);
}

.download-btn:hover {
  transform: translateY(-3px);
  box-shadow: 0 15px 20px -5px rgba(0, 0, 0, 0.3);
}

.not-found {
  text-align: center;
  padding: 3rem 0;
}

.not-found p {
  font-size: 1.2rem;
  margin-bottom: 2rem;
  opacity: 0.9;
}

.back-btn.large {
  padding: 0.8rem 2rem;
  font-size: 1rem;
}

/* 移动端适应 */
@media (max-width: 640px) {
  .content {
    padding: 1rem;
  }
  .dataset-name {
    font-size: 2rem;
  }
  .info-grid {
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
  }
}
</style>
