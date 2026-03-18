<template>
  <div class="content">
    <div class="detail-card ui-surface-glass">
      <div class="card-header">
        <button class="back-btn ui-btn ui-btn-pill" @click="goBack">
          ← 返回列表
        </button>
      </div>

      <div v-if="dataset" class="dataset-info">
        <h1 class="dataset-name">{{ dataset.name }}</h1>
        <p class="dataset-description">{{ dataset.description }}</p>

        <div class="info-grid ui-surface-white">
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
          <a
            :href="dataset.downloadUrl"
            class="download-btn ui-btn ui-btn-pill ui-btn-gradient ui-btn-hover-lift"
            target="_blank"
            rel="noopener"
          >
            下载数据集
          </a>
        </div>
      </div>

      <div v-else class="not-found">
        <p>数据集不存在或ID错误</p>
        <button
          class="back-btn large ui-btn ui-btn-pill ui-btn-gradient ui-btn-hover-lift"
          @click="goBack"
        >
          返回列表
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from "vue-router";
import { computed } from "vue";

// 模拟数据集详情数据（与 DataSet.vue 中的数据集对应）
const datasets = [
  {
    id: 1,
    name: "Prompt Injection Dataset",
    description:
      "包含多种提示注入攻击样本，用于测试智能体对恶意指令的防护能力。数据集包含 10,000 条精心构造的提示，覆盖常见攻击模式。",
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
      "模拟越狱攻击场景，评估智能体在违规请求下的行为安全性。数据集包含 8,000 条越狱尝试，覆盖多种绕过策略。",
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
/* 全局重置动画 */
.content {
  max-width: 800px;
  padding: 2rem;
}

.detail-card {
  border-radius: 2rem;
  padding: 2rem;
}

.card-header {
  margin-bottom: 1.5rem;
}

.back-btn {
  padding: 0.5rem 1.2rem;
  font-size: 0.95rem;
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
  border-radius: 1.2rem;
  padding: 1.5rem;
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
  padding: 0.9rem 2.5rem;
  text-decoration: none;
  transition:
    transform 0.2s,
    box-shadow 0.2s;
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

/* 绉诲姩绔€傚簲 */
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
