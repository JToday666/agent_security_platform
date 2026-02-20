<template>
  <Navbar />
  <main class="page-container leaderboard-page">
    <div class="content">
      <h1 class="page-title">排行榜</h1>
      <p class="page-subtitle">查看公开智能体在各数据集上的表现排名。</p>

      <!-- 筛选区域（UI占位，无实际功能） -->
      <div class="filter-bar">
        <select class="filter-select">
          <option>所有数据集</option>
          <option>Prompt Injection Dataset</option>
          <option>Jailbreak Dataset</option>
        </select>
        <select class="filter-select">
          <option>所有智能体</option>
          <option>智能体 A</option>
          <option>智能体 B</option>
        </select>
        <button class="filter-btn">筛选</button>
      </div>

      <!-- 排名表格 -->
      <div class="rank-table">
        <div class="table-header">
          <span>排名</span>
          <span>智能体名称</span>
          <span>所属数据集</span>
          <span>评分</span>
        </div>
        <div class="table-row" v-for="n in 5" :key="n">
          <span>{{ n }}</span>
          <span>智能体 Alpha-{{ n }}</span>
          <span>Prompt Injection Dataset</span>
          <span>{{ (Math.random() * 100).toFixed(2) }}</span>
        </div>
      </div>
      <p class="coming-soon">更多排名数据即将上线，敬请期待。</p>
    </div>
  </main>
</template>

<script setup lang="ts">
import Navbar from "@/components/NavBar.vue";
</script>

<style scoped>
.page-container {
  min-height: 100vh;
  padding-top: 70px;
  background: linear-gradient(145deg, #667eea 0%, #764ba2 100%);
  display: flex;
  justify-content: center;
}

.content {
  max-width: 1000px;
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
  margin-bottom: 2rem;
  opacity: 0.9;
}

/* 筛选条 */
.filter-bar {
  display: flex;
  gap: 1rem;
  margin-bottom: 2.5rem;
  flex-wrap: wrap;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(5px);
  padding: 1rem 1.5rem;
  border-radius: 50px;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.filter-select {
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
  padding: 0.6rem 1.2rem;
  border-radius: 30px;
  font-size: 0.95rem;
  cursor: pointer;
  outline: none;
  flex: 1 1 180px;
}

.filter-select option {
  background: #4a5568;
  color: white;
}

.filter-btn {
  background: white;
  color: #667eea;
  border: none;
  padding: 0.6rem 2rem;
  border-radius: 30px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s;
}

.filter-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 15px rgba(0, 0, 0, 0.2);
}

/* 排名表格 */
.rank-table {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  border-radius: 1.5rem;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.2);
  margin-bottom: 2rem;
}

.table-header {
  display: grid;
  grid-template-columns: 80px 1fr 1.5fr 100px;
  padding: 1.2rem 1.5rem;
  background: rgba(255, 255, 255, 0.2);
  font-weight: 600;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}

.table-row {
  display: grid;
  grid-template-columns: 80px 1fr 1.5fr 100px;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  transition: background 0.2s;
}

.table-row:last-child {
  border-bottom: none;
}

.table-row:hover {
  background: rgba(255, 255, 255, 0.1);
}

.coming-soon {
  text-align: center;
  font-size: 1rem;
  opacity: 0.8;
  margin-top: 1rem;
}

@media (max-width: 640px) {
  .page-title {
    font-size: 2.2rem;
  }
  .table-header,
  .table-row {
    grid-template-columns: 50px 1fr 1.2fr 70px;
    font-size: 0.85rem;
    padding: 0.8rem 1rem;
  }
  .filter-bar {
    border-radius: 20px;
    padding: 0.8rem;
  }
}
</style>
