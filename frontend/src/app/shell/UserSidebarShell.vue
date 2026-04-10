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
        v-for="item in SIDEBAR_ITEMS"
        :key="item.key"
        v-bind="getLinkStateProps(item)"
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
import type { RouteLocationRaw } from "vue-router";
import AppIcon from "@/shared/ui/AppIcon.vue";
import { RouteLocation } from "@/app/router/RouteNames";

interface SidebarItem {
  key: string;
  label: string;
  icon: string;
  to: RouteLocationRaw;
  exact?: boolean;
}

const SIDEBAR_ITEMS: SidebarItem[] = [
  {
    key: "records",
    label: "评测记录",
    icon: "lucide:clipboard-list",
    to: RouteLocation.userCenter,
    exact: true,
  },
  {
    key: "submit",
    label: "提交测评",
    icon: "lucide:file-plus-2",
    to: RouteLocation.agentSubmit,
  },
  {
    key: "profile",
    label: "个人资料",
    icon: "lucide:square-pen",
    to: RouteLocation.userProfile,
  },
  {
    key: "dataset",
    label: "评测目录",
    icon: "lucide:database",
    to: RouteLocation.datasetList,
  },
  {
    key: "leaderboard",
    label: "排行榜",
    icon: "lucide:trophy",
    to: RouteLocation.leaderboard,
  },
  {
    key: "contact",
    label: "联系我们",
    icon: "lucide:mail",
    to: RouteLocation.contact,
  },
];

const collapsed = ref(false);

const getLinkStateProps = (item: SidebarItem) =>
  item.exact
    ? { activeClass: "active", exactActiveClass: "active" }
    : { activeClass: "active" };

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

<style scoped>
.user-sidebar {
  position: fixed;
  left: 0;
  top: var(--nav-height);
  height: calc(100vh - var(--nav-height));
  transition: width 0.3s ease;
  width: var(--sidebar-width);
  z-index: var(--z-sidebar);
  display: flex;
  flex-direction: column;
  padding: 0.75rem;
  border-right: 1px solid rgba(226, 232, 240, 0.82);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.82), rgba(248, 250, 252, 0.92));
  box-shadow:
    18px 0 40px -36px rgba(15, 23, 42, 0.35),
    inset -1px 0 0 rgba(255, 255, 255, 0.55);
}

.user-sidebar.collapsed {
  width: var(--sidebar-width-collapsed);
}

.toggle-btn {
  align-self: flex-end;
  width: 2.2rem;
  height: 2.2rem;
  border-radius: 999px;
  border: 1px solid rgba(203, 213, 225, 0.88);
  background: rgba(255, 255, 255, 0.92);
  color: #64748b;
  margin: 0 0 0.55rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition:
    background 0.2s ease,
    color 0.2s ease,
    border-color 0.2s ease,
    transform 0.2s ease;
}

.toggle-btn:hover {
  transform: translateY(-1px);
  background: #ffffff;
  border-color: rgba(96, 165, 250, 0.3);
  color: #2563eb;
}

.toggle-icon {
  width: 1rem;
  height: 1rem;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.95rem;
  padding: 0.88rem 1rem;
  border-radius: 1rem;
  border: 1px solid transparent;
  color: #334155;
  text-decoration: none;
  transition:
    background 0.2s ease,
    color 0.2s ease,
    border-color 0.2s ease,
    transform 0.2s ease,
    box-shadow 0.2s ease;
  white-space: nowrap;
  overflow: hidden;
}

.nav-item:hover {
  transform: translateY(-1px);
  background: rgba(255, 255, 255, 0.88);
  border-color: rgba(226, 232, 240, 0.88);
  color: #2563eb;
}

.nav-item.active {
  background:
    linear-gradient(135deg, rgba(219, 234, 254, 0.78), rgba(255, 255, 255, 0.98));
  border-color: rgba(96, 165, 250, 0.28);
  color: #2563eb;
  font-weight: 600;
  box-shadow: 0 14px 30px -28px rgba(37, 99, 235, 0.45);
}

.icon {
  width: 1.18rem;
  height: 1.18rem;
  min-width: 1.18rem;
  flex-shrink: 0;
}

.text {
  font-size: 0.95rem;
  font-weight: 600;
  opacity: 0.94;
}

.user-sidebar.collapsed .nav-item {
  justify-content: center;
  padding: 0.88rem 0;
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
