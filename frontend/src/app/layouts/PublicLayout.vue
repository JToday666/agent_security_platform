<template>
  <NavBarShell />
  <main class="public-layout">
    <router-view v-slot="{ Component, route }">
      <Transition name="page-shell" mode="out-in">
        <component :is="Component" :key="route.fullPath" />
      </Transition>
    </router-view>
  </main>
</template>

<script setup lang="ts">
import NavBarShell from "@/app/shell/NavBarShell.vue";
</script>
