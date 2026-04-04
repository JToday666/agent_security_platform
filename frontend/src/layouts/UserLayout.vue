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
