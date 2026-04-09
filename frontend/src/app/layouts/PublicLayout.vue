<template>
  <NavBarShell />
  <main class="public-layout">
    <router-view />
  </main>
</template>

<script setup lang="ts">
import NavBarShell from "@/app/shell/NavBarShell.vue";
</script>
