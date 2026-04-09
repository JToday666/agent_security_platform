<template>
  <aside class="user-sidebar" :class="{ collapsed }">
    <button
      class="toggle-btn"
      type="button"
      :aria-label="collapsed ? '展开侧边栏' : '收起侧边栏'"
      @click="collapsed = !collapsed"
    >
      <AppIcon
        :icon="collapsed ? 'lucide:chevrons-right' : 'lucide:chevrons-left'"
        class="toggle-icon"
      />
    </button>

    <nav class="sidebar-nav">
      <router-link
        :to="RouteLocation.userCenter"
        class="nav-item"
        active-class="active"
        exact-active-class="active"
      >
        <AppIcon icon="lucide:clipboard-list" class="icon" />
        <span v-if="!collapsed" class="text">评测记录</span>
      </router-link>
      <router-link :to="RouteLocation.agentSubmit" class="nav-item" active-class="active">
        <AppIcon icon="lucide:bot" class="icon" />
        <span v-if="!collapsed" class="text">提交智能体</span>
      </router-link>
      <router-link :to="RouteLocation.userProfile" class="nav-item" active-class="active">
        <AppIcon icon="lucide:square-pen" class="icon" />
        <span v-if="!collapsed" class="text">个人资料</span>
      </router-link>
      <router-link :to="RouteLocation.datasetList" class="nav-item" active-class="active">
        <AppIcon icon="lucide:database" class="icon" />
        <span v-if="!collapsed" class="text">评测目录</span>
      </router-link>
      <router-link :to="RouteLocation.leaderboard" class="nav-item" active-class="active">
        <AppIcon icon="lucide:trophy" class="icon" />
        <span v-if="!collapsed" class="text">排行榜</span>
      </router-link>
      <router-link :to="RouteLocation.contact" class="nav-item" active-class="active">
        <AppIcon icon="lucide:mail" class="icon" />
        <span v-if="!collapsed" class="text">联系我们</span>
      </router-link>
    </nav>
  </aside>
</template>

<script setup lang="ts">
import { ref } from "vue";
import AppIcon from "@/shared/ui/AppIcon.vue";
import { RouteLocation } from "@/app/router/RouteNames";

const collapsed = ref(false);
</script>

<style scoped>
.user-sidebar {
  position: fixed;
  left: 0;
  top: var(--nav-height);
  height: calc(100vh - var(--nav-height));
  border-right: 1px solid rgba(0, 0, 0, 0.05);
  box-shadow: 5px 0 20px rgba(0, 0, 0, 0.03);
  transition: width 0.3s ease;
  width: var(--sidebar-width);
  z-index: var(--z-sidebar);
  display: flex;
  flex-direction: column;
}

.user-sidebar.collapsed {
  width: var(--sidebar-width-collapsed);
}

.toggle-btn {
  align-self: flex-end;
  background: rgba(0, 0, 0, 0.03);
  border: 1px solid rgba(0, 0, 0, 0.08);
  color: #64748b;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  margin: 1rem 1rem 0.5rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition:
    background 0.2s ease,
    color 0.2s ease;
}

.toggle-btn:hover {
  background: rgba(0, 0, 0, 0.06);
  color: #2563eb;
}

.toggle-icon {
  width: 1rem;
  height: 1rem;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  padding: 0.5rem 0;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.8rem 1.5rem;
  color: #334155;
  text-decoration: none;
  transition:
    background 0.2s ease,
    color 0.2s ease;
  white-space: nowrap;
  overflow: hidden;
  border-left: 4px solid transparent;
}

.nav-item:hover {
  background: rgba(0, 0, 0, 0.02);
  color: #2563eb;
}

.nav-item.active {
  background: rgba(59, 130, 246, 0.05);
  border-left-color: #2563eb;
  color: #2563eb;
  font-weight: 500;
}

.icon {
  width: 1.35rem;
  height: 1.35rem;
  min-width: 24px;
  flex-shrink: 0;
}

.text {
  font-size: 1rem;
  font-weight: 500;
  opacity: 0.9;
}

.user-sidebar.collapsed .nav-item {
  justify-content: center;
  padding: 0.8rem 0;
}

.user-sidebar.collapsed .text {
  display: none;
}

@media (max-width: 1024px) {
  .user-sidebar {
    display: none;
  }
}
</style>