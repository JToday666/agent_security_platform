<template>
  <Navbar />
  <main class="page-container user-center">
    <!-- 左侧侧边栏 -->
    <UserSidebar />
    <div class="content-area">
      <div class="records-card">
        <h1 class="page-title">评测记录</h1>
        <p class="page-subtitle">您提交过的所有智能体评测历史。</p>

        <div class="records-list">
          <div v-for="record in records" :key="record.id" class="record-item">
            <div class="record-info">
              <h3>{{ record.name }}</h3>
              <p>数据集：{{ record.dataset }} · 提交时间：{{ record.date }}</p>
            </div>
            <router-link :to="`/report/${record.id}`" class="view-btn"> 查看报告 → </router-link>
          </div>
        </div>

        <div v-if="records.length === 0" class="empty-state">
          <p>您还没有提交过智能体评测。</p>
          <router-link to="/submit" class="btn">立即提交</router-link>
        </div>
      </div>
    </div>
  </main>
</template>

<script setup lang="ts">
import Navbar from "@/components/NavBar.vue";
import UserSidebar from "@/components/UserSidebar.vue";

const records = [
  {
    id: 1,
    name: "智能体 Alpha-1",
    dataset: "Prompt Injection Dataset",
    date: "2025-02-10",
  },
  {
    id: 2,
    name: "智能体 Beta-2",
    dataset: "Jailbreak Dataset",
    date: "2025-02-12",
  },
];
</script>

<style scoped>
.page-container {
  min-height: 100vh;
  padding-top: 70px;
  background: linear-gradient(145deg, #667eea 0%, #764ba2 100%);
  display: flex;
}

.content-area {
  flex: 1;
  margin-left: 240px; /* 与侧边栏宽度相同 */
  padding: 2rem;
  transition: margin-left 0.3s ease;
}

/* 当侧边栏收起时，调整左边距 */
.user-sidebar.collapsed ~ .content-area {
  margin-left: 70px;
}

.records-card {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  border-radius: 2rem;
  border: 1px solid rgba(255, 255, 255, 0.2);
  padding: 2rem 2.5rem;
  color: white;
  box-shadow: 0 20px 35px -8px rgba(0, 0, 0, 0.2);
  max-width: 900px;
  margin: 0 auto;
}

.page-title {
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  text-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.page-subtitle {
  font-size: 1.1rem;
  margin-bottom: 2rem;
  opacity: 0.9;
}

.records-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.record-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(255, 255, 255, 0.1);
  padding: 1.2rem 1.5rem;
  border-radius: 1.2rem;
  border: 1px solid rgba(255, 255, 255, 0.15);
  transition:
    transform 0.2s,
    background 0.2s;
}

.record-item:hover {
  transform: translateX(5px);
  background: rgba(255, 255, 255, 0.15);
}

.record-info h3 {
  font-size: 1.3rem;
  font-weight: 600;
  margin-bottom: 0.3rem;
}

.record-info p {
  font-size: 0.95rem;
  opacity: 0.8;
}

.view-btn {
  background: white;
  color: #667eea;
  padding: 0.5rem 1.2rem;
  border-radius: 30px;
  text-decoration: none;
  font-weight: 500;
  transition:
    transform 0.2s,
    box-shadow 0.2s;
}

.view-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 15px rgba(0, 0, 0, 0.2);
}

.empty-state {
  text-align: center;
  padding: 3rem 0;
}

.empty-state p {
  font-size: 1.1rem;
  margin-bottom: 1.5rem;
  opacity: 0.9;
}

.btn {
  display: inline-block;
  background: white;
  color: #667eea;
  padding: 0.8rem 2rem;
  border-radius: 50px;
  text-decoration: none;
  font-weight: 600;
  transition: transform 0.2s;
}

.btn:hover {
  transform: translateY(-2px);
}

@media (max-width: 768px) {
  .content-area {
    margin-left: 0;
    padding: 1rem;
  }
}
</style>
