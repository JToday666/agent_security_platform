<template>
  <Navbar />
  <main class="user-layout">
    <UserSidebar />
    <div class="content-area">
      <router-view />
    </div>
  </main>
</template>

<script setup lang="ts">
// 用户布局统一承载侧边导航和登录后页面内容。
import Navbar from "@/components/navigation/NavBar.vue";
import UserSidebar from "@/components/navigation/UserSidebar.vue";
</script>

<style scoped>
.content-area {
  flex: 1;
  margin-left: var(--sidebar-width);
  padding: var(--space-page-x);
  transition: margin-left var(--duration-base) ease;
  position: relative;
  z-index: var(--z-content);
  animation: fadeInUp var(--duration-fade-in) ease;
}

/* 控制侧边栏折叠状态来自动调整内容区域边距 */
.user-layout .user-sidebar.collapsed ~ .content-area {
  margin-left: var(--sidebar-width-collapsed);
}

@media (max-width: 768px) {
  .content-area {
    margin-left: 0;
    padding: var(--space-page-x-mobile);
  }
}
</style>
