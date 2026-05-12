<template>
  <div ref="menuRoot" class="desktop-nav-overflow">
    <button
      class="overflow-trigger"
      type="button"
      aria-haspopup="menu"
      :aria-expanded="open ? 'true' : 'false'"
      :aria-label="label"
      @click="toggleMenu"
    >
      <span class="overflow-trigger__label">{{ label }}</span>
      <AppIcon icon="app:control.more" class="overflow-trigger__icon" />
    </button>

    <div v-if="open" class="overflow-menu" role="menu">
      <router-link
        v-for="item in items"
        :key="`desktop-overflow-${item.key}`"
        v-bind="getNavLinkStateProps(item)"
        :to="item.to"
        class="overflow-menu__item"
        role="menuitem"
        :aria-label="item.label"
        :title="item.label"
        @click="closeMenu"
      >
        <AppIcon :icon="item.icon" class="overflow-menu__icon" />
        <span>{{ item.label }}</span>
      </router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from "vue";
import { getNavLinkStateProps } from "@/app/shell/nav-link-state";
import type { AppNavItem } from "@/app/shell/nav-items";
import AppIcon from "@/shared/ui/branding/AppIcon.vue";

defineProps<{
  items: AppNavItem[];
  label: string;
}>();

const open = ref(false);
const menuRoot = ref<HTMLElement | null>(null);

const closeMenu = () => {
  open.value = false;
};

const toggleMenu = () => {
  open.value = !open.value;
};

const handleDocumentClick = (event: MouseEvent) => {
  if (!menuRoot.value?.contains(event.target as Node)) {
    closeMenu();
  }
};

const handleKeydown = (event: KeyboardEvent) => {
  if (event.key === "Escape") {
    closeMenu();
  }
};

onMounted(() => {
  document.addEventListener("click", handleDocumentClick);
  document.addEventListener("keydown", handleKeydown);
});

onUnmounted(() => {
  document.removeEventListener("click", handleDocumentClick);
  document.removeEventListener("keydown", handleKeydown);
});
</script>

<style scoped lang="scss">
.desktop-nav-overflow {
  position: relative;
  display: inline-flex;
  align-items: center;
  min-width: 0;
}

.overflow-trigger {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  min-height: 2.6rem;
  max-width: 9.6rem;
  min-width: 0;
  padding: 0.46rem 0.72rem;
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: var(--radius-pill);
  background: rgba(255, 255, 255, 0.78);
  box-shadow: 0 16px 30px -28px rgba(15, 23, 42, 0.14);
  color: #334155;
  cursor: pointer;
  font-size: 0.86rem;
  font-weight: 700;
}

.overflow-trigger:hover,
.overflow-trigger:focus-visible {
  border-color: rgba(99, 102, 241, 0.2);
  color: var(--color-primary);
}

.overflow-trigger__label {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.overflow-trigger__icon {
  flex-shrink: 0;
  width: 0.95rem;
  height: 0.95rem;
}

.overflow-menu {
  position: absolute;
  top: calc(100% + 0.55rem);
  right: 0;
  z-index: calc(var(--z-nav) + 1);
  display: flex;
  min-width: 13.5rem;
  max-width: min(24rem, calc(100vw - 2rem));
  flex-direction: column;
  gap: 0.2rem;
  padding: 0.48rem;
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: var(--radius-card-sm);
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 24px 44px -28px rgba(15, 23, 42, 0.28);
  backdrop-filter: blur(var(--blur-10));
}

.overflow-menu__item {
  display: flex;
  align-items: center;
  gap: 0.62rem;
  min-width: 0;
  padding: 0.68rem 0.72rem;
  border-radius: 0.85rem;
  color: #334155;
  font-size: 0.9rem;
  font-weight: 600;
  text-decoration: none;
}

.overflow-menu__item:hover,
.overflow-menu__item.active {
  background: rgba(219, 234, 254, 0.66);
  color: var(--color-primary);
}

.overflow-menu__item span {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.overflow-menu__icon {
  flex-shrink: 0;
  width: 1rem;
  height: 1rem;
}
</style>
