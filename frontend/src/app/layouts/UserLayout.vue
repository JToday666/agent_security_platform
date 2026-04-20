<template>
  <NavBarShell />
  <main class="user-layout layout-app-shell">
    <UserSidebarShell />
    <div class="layout-app-content">
      <router-view />
    </div>
  </main>
</template>

<script setup lang="ts">
import NavBarShell from "@/app/shell/NavBarShell.vue";
import UserSidebarShell from "@/app/shell/UserSidebarShell.vue";
</script>

<style scoped lang="scss">
.user-layout {
  min-height: calc(100vh - var(--nav-height));
}
</style>
