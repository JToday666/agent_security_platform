<template>
  <NavBarShell />
  <main v-if="showSidebar" class="public-layout layout-app-shell">
    <UserSidebarShell />
    <div class="layout-app-content">
      <router-view />
    </div>
  </main>
  <main v-else class="public-layout">
    <router-view />
  </main>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { storeToRefs } from "pinia";
import { useRoute } from "vue-router";
import NavBarShell from "@/app/shell/NavBarShell.vue";
import UserSidebarShell from "@/app/shell/UserSidebarShell.vue";
import { ROUTE_NAME } from "@/app/router/RouteNames";
import { useUserStore } from "@/modules/account/stores/UserStore";

const route = useRoute();
const userStore = useUserStore();
const { isLogin } = storeToRefs(userStore);

const showSidebar = computed(
  () => isLogin.value && route.name !== ROUTE_NAME.HOME_PAGE,
);
</script>
