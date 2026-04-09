<template>
  <div class="content not-found-page layout-page-shell">
    <PageHeroCard
      eyebrow="404"
      title="页面未找到"
      description="当前地址不是系统支持的页面路径。历史旧入口已移除，请从当前导航或下方入口重新进入。"
    />

    <section class="layout-page-panel layout-page-panel--md ui-surface-white not-found-card">
      <h2>可用入口</h2>
      <p>
        前端当前仅保留规范化的新路由，例如评测目录、评测记录、提交智能体、评测详情和个人资料页面。
      </p>
      <div class="actions">
        <router-link
          :to="RouteLocation.home"
          class="ui-btn ui-btn-pill"
        >
          返回首页
        </router-link>
        <router-link
          :to="RouteLocation.datasetList"
          class="ui-btn ui-btn-pill ui-btn-gradient ui-btn-hover-lift"
        >
          查看评测目录
        </router-link>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import PageHeroCard from "@/shared/ui/PageHeroCard.vue";
import { RouteLocation } from "@/app/router/RouteNames";
</script>

<style scoped>
.not-found-card {
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
}

.not-found-card h2 {
  margin: 0;
  color: #0f172a;
  font-size: 1.2rem;
}

.not-found-card p {
  margin: 0;
  color: #475569;
  line-height: 1.8;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.8rem;
  margin-top: 0.2rem;
}

.actions :deep(a) {
  text-decoration: none;
}
</style>
