<template>
  <div class="content">
    <h1 class="page-title">排行榜</h1>
    <p class="page-subtitle">查看公开智能体在各数据集上的表现排名。</p>

    <!-- 筛选区域 -->
    <div class="filter-bar ui-surface-white">
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
      <button
        class="filter-btn ui-btn ui-btn-pill ui-btn-gradient ui-btn-hover-lift"
      >
        筛选
      </button>
    </div>

    <!-- 排名表格 -->
    <div class="rank-table ui-surface-white">
      <div class="table-header">
        <span>排名</span>
        <span>智能体名称</span>
        <span>所属数据集</span>
        <span>得分</span>
      </div>
      <div class="table-row" v-for="n in 5" :key="n">
        <span>{{ n }}</span>
        <span>智能体 Alpha-{{ n }}</span>
        <span>Prompt Injection Dataset</span>
        <span>{{ (Math.random() * 100).toFixed(2) }}</span>
      </div>
    </div>
    <p class="coming-soon">更多排名数据即将上线，敬请期待！</p>
  </div>
</template>

<script setup lang="ts"></script>

<style scoped>
/* 全局重置动画 */
.content {
  max-width: 1000px;
  padding: 3rem 2rem;
}

.page-title {
  font-size: 3rem;
  font-weight: 800;
  margin-bottom: 0.5rem;
}

.page-subtitle {
  font-size: 1.2rem;
  margin-bottom: 2rem;
}

/* 筛选条件 */
.filter-bar {
  display: flex;
  gap: 1rem;
  margin-bottom: 2.5rem;
  flex-wrap: wrap;
  background: white;
  padding: 1rem 1.5rem;
  border-radius: 50px;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05);
  border: 1px solid rgba(0, 0, 0, 0.02);
}

.filter-select {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  color: #1e293b;
  padding: 0.6rem 1.2rem;
  border-radius: 30px;
  font-size: 0.95rem;
  cursor: pointer;
  outline: none;
  flex: 1 1 180px;
  transition:
    border-color 0.2s,
    box-shadow 0.2s;
}

.filter-select:focus {
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.filter-select option {
  background: white;
  color: #1e293b;
}

.filter-btn {
  border: none;
  padding: 0.6rem 2rem;
  font-weight: 600;
  transition:
    transform 0.2s,
    box-shadow 0.2s;
}

/* 排名表格 */
.rank-table {
  border-radius: 1.5rem;
  overflow: hidden;
  box-shadow: 0 15px 30px -10px rgba(0, 0, 0, 0.1);
  margin-bottom: 2rem;
}

.table-header {
  display: grid;
  grid-template-columns: 80px 1fr 1.5fr 100px;
  padding: 1.2rem 1.5rem;
  background: #f8fafc;
  font-weight: 600;
  color: #0f172a;
  border-bottom: 1px solid #e2e8f0;
}

.table-row {
  display: grid;
  grid-template-columns: 80px 1fr 1.5fr 100px;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #e2e8f0;
  transition: background 0.2s;
  color: #334155;
}

.table-row:last-child {
  border-bottom: none;
}

.table-row:hover {
  background: #f1f5f9;
}

.coming-soon {
  text-align: center;
  font-size: 1rem;
  color: #64748b;
  margin-top: 1rem;
}

/* 绉诲姩绔€傚簲 */
@media (max-width: 640px) {
  .content {
    padding: 2rem 1rem;
  }

  .page-title {
    font-size: 2.5rem;
  }

  .page-subtitle {
    font-size: 1rem;
  }

  .filter-bar {
    border-radius: 20px;
    padding: 0.8rem;
    flex-direction: column;
  }

  .filter-select,
  .filter-btn {
    width: 100%;
  }

  .table-header,
  .table-row {
    grid-template-columns: 50px 1fr 1.2fr 70px;
    font-size: 0.85rem;
    padding: 0.8rem 1rem;
  }
}
</style>
