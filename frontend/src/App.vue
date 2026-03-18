<template>
	<router-view />
	<LoginDialog />
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from "vue";
import LoginDialog from "@/components/LoginDialog.vue";
import { useUserStore } from "@/store/user";

const userStore = useUserStore();

const handleUnauthorized = () => {
	userStore.handleUnauthorized();
};

onMounted(() => {
	window.addEventListener("unauthorized", handleUnauthorized);
});

onUnmounted(() => {
	window.removeEventListener("unauthorized", handleUnauthorized);
});
</script>
