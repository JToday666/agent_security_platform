<template>
  <Navbar />
  <main class="public-layout">
    <router-view />
  </main>
</template>

<script setup lang="ts">
// 公共布局只负责顶部导航和公共页面内容承载。
import Navbar from "@/components/navigation/NavBar.vue";
</script>
