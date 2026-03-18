<template>
  <Navbar />
  <main class="public-layout">
    <router-view />
  </main>
</template>

<script setup lang="ts">
import Navbar from "@/components/NavBar.vue";
</script>
