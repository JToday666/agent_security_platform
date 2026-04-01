<template>
  <router-view />
  <LoginDialog />
</template>

<script setup lang="ts">
// 登录弹窗挂在应用根节点，便于路由守卫和全局未授权事件直接唤起。
import LoginDialog from "@/components/dialog/LoginDialog.vue";
</script>
