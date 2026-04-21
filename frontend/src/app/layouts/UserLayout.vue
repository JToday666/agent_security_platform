<template>
  <NavBarShell />
  <main class="user-layout layout-app-shell">
    <UserSidebarShell />
    <div class="layout-app-content">
      <router-view v-slot="{ Component, route }">
        <Transition name="page-shell" mode="out-in">
          <component :is="Component" :key="route.fullPath" />
        </Transition>
      </router-view>
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
  display: grid;
  grid-template-columns:
    var(--sidebar-active-width, var(--sidebar-width))
    minmax(0, 1fr);
  align-items: start;
  gap: 1rem;
  padding-inline: 1rem 1.1rem;
}

@media (max-width: 1024px) {
  .user-layout {
    grid-template-columns: minmax(0, 1fr);
    gap: 0;
    padding-inline: 0;
  }
}
</style>
