<template>
  <aside class="user-sidebar" :class="{ collapsed }">
    <div class="sidebar-top">
      <strong v-if="!collapsed" class="sidebar-title">工作台</strong>

      <button
        class="toggle-btn"
        type="button"
        :aria-label="collapsed ? '展开侧边栏' : '收起侧边栏'"
        @click="collapsed = !collapsed"
      >
        <AppIcon
          :icon="collapsed ? 'lucide:panel-left-open' : 'lucide:panel-left-close'"
          class="toggle-icon"
        />
      </button>
    </div>

    <nav class="sidebar-nav">
      <router-link
        v-for="item in WORKSPACE_SIDEBAR_ITEMS"
        :key="item.key"
        v-bind="getNavLinkStateProps(item)"
        :to="item.to"
        class="nav-item"
      >
        <AppIcon :icon="item.icon" class="icon" />
        <span v-if="!collapsed" class="text">{{ item.label }}</span>
      </router-link>
    </nav>

  </aside>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from "vue";
import AppIcon from "@/shared/ui/branding/AppIcon.vue";
import { WORKSPACE_SIDEBAR_ITEMS } from "@/app/shell/nav-items";
import { getNavLinkStateProps } from "@/app/shell/nav-link-state";

const collapsed = ref(false);


const syncSidebarWidth = () => {
  document.documentElement.style.setProperty(
    "--sidebar-active-width",
    collapsed.value
      ? "var(--sidebar-width-collapsed)"
      : "var(--sidebar-width)",
  );
};

watch(collapsed, syncSidebarWidth);

onMounted(() => {
  syncSidebarWidth();
});

onUnmounted(() => {
  document.documentElement.style.removeProperty("--sidebar-active-width");
});
</script>

<style scoped lang="scss">
.user-sidebar {
  position: sticky;
  top: calc(var(--nav-height) + 1rem);
  z-index: var(--z-sidebar);
  width: 100%;
  max-height: calc(100vh - var(--nav-height) - 2rem);
  align-self: start;
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  min-width: 0;
  overflow-y: auto;
  padding: 1rem 0.85rem 1rem 0.95rem;
  border: 1px solid rgba(148, 163, 184, 0.14);
  border-radius: 1.35rem;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.9), rgba(255, 255, 255, 0.78));
  box-shadow: var(--shadow-glass-card);
  transition:
    padding var(--duration-base) var(--ease-standard),
    border-color var(--duration-fast) var(--ease-standard);
}

.user-sidebar.collapsed {
  padding-inline: 0.7rem;
}

.sidebar-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.8rem;
  margin-bottom: 1rem;
}

.user-sidebar.collapsed .sidebar-top {
  justify-content: flex-end;
}

.sidebar-title {
  color: var(--color-text-dark);
  font-size: 1rem;
  font-weight: 700;
}

.toggle-btn {
  width: 2.25rem;
  height: 2.25rem;
  flex-shrink: 0;
  border-radius: 999px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  background: rgba(255, 255, 255, 0.92);
  color: var(--color-text-subtle);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: var(--shadow-control);
  transition:
    transform var(--duration-fast) var(--ease-standard),
    color var(--duration-fast) var(--ease-standard),
    border-color var(--duration-fast) var(--ease-standard);
}

.toggle-btn:hover {
  transform: translateY(-1px);
  color: var(--color-primary);
  border-color: rgba(99, 102, 241, 0.24);
}

.toggle-icon {
  width: 1rem;
  height: 1rem;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 0.38rem;
  min-width: 0;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.88rem;
  padding: 0.85rem 0.95rem;
  border-radius: 1rem;
  border: 1px solid transparent;
  color: #334155;
  text-decoration: none;
  transition:
    transform var(--duration-fast) var(--ease-standard),
    border-color var(--duration-fast) var(--ease-standard),
    background var(--duration-fast) var(--ease-standard),
    color var(--duration-fast) var(--ease-standard),
    box-shadow var(--duration-fast) var(--ease-standard);
}

.nav-item:hover {
  transform: translateY(-1px);
  border-color: rgba(148, 163, 184, 0.18);
  background: rgba(255, 255, 255, 0.82);
  color: var(--color-primary);
}

.nav-item.active {
  color: var(--color-primary);
  background: linear-gradient(135deg, rgba(219, 234, 254, 0.78), rgba(255, 255, 255, 0.98));
  border-color: rgba(99, 102, 241, 0.16);
  box-shadow: 0 18px 28px -26px rgba(79, 70, 229, 0.46);
}

.icon {
  width: 1.1rem;
  height: 1.1rem;
  min-width: 1.1rem;
  flex-shrink: 0;
}

.text {
  font-size: 0.94rem;
  font-weight: 600;
  white-space: nowrap;
}

.user-sidebar.collapsed .nav-item {
  justify-content: center;
  padding-inline: 0.45rem;
}

@media (max-width: 1024px) {
  .user-sidebar {
    display: none;
  }
}
</style>
