<template>
  <router-view />
  <LoginDialog />
</template>

<script setup lang="ts">
import LoginDialog from "@/modules/account/components/LoginDialog.vue";
</script>
