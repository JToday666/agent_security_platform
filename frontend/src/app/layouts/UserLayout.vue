<template>
  <NavBarShell />
  <main class="user-layout">
    <UserSidebarShell />
    <div class="content-area">
      <router-view />
    </div>
  </main>
</template>

<script setup lang="ts">
import NavBarShell from "@/app/shell/NavBarShell.vue";
import UserSidebarShell from "@/app/shell/UserSidebarShell.vue";
</script>

<style scoped>
.user-layout {
  min-height: calc(100vh - var(--nav-height));
}

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

@media (max-width: 1024px) {
  .content-area {
    margin-left: 0;
    padding: var(--space-page-x-mobile);
  }
}
</style>