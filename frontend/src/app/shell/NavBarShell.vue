<template>
  <nav class="navbar" :class="[`navbar--${shellContext}`, { hidden: !isVisible && !mobileMenuOpen }]">
    <div class="nav-container">
      <div class="brand-cluster">
        <router-link
          :to="RouteLocation.home"
          class="brand-mark ui-glow-frame"
          aria-label="返回首页"
        >
          <BrandLogo
            class="brand-logo"
            alt="智能体安全评测平台标志"
            :priority="true"
          />
        </router-link>

        <router-link :to="RouteLocation.home" class="brand-title ui-title-gradient">
          智能体安全评测平台
        </router-link>
      </div>

      <div class="nav-links nav-links--primary">
        <router-link
          v-for="item in mainNavItems"
          :key="`desktop-main-${item.key}`"
          v-bind="getNavLinkStateProps(item)"
          :to="item.to"
          class="nav-link"
        >
          <AppIcon :icon="item.icon" class="nav-link-icon" />
          <span>{{ item.label }}</span>
        </router-link>
      </div>

      <div v-if="secondaryNavItems.length" class="nav-links nav-links--secondary">
        <router-link
          v-for="item in secondaryNavItems"
          :key="`desktop-secondary-${item.key}`"
          v-bind="getNavLinkStateProps(item)"
          :to="item.to"
          class="nav-link nav-link--secondary nav-link--with-icon"
        >
          <AppIcon :icon="item.icon" class="nav-link-icon" />
          <span>{{ item.label }}</span>
        </router-link>
      </div>

      <div class="nav-actions">
        <UiButton
          v-if="!isLogin && shellContext === 'public'"
          class="cta-btn"
          as="button"
          variant="primary"
          leading-icon="lucide:log-in"
          @click="openLoginDialog"
        >
          <span>登录 / 注册</span>
        </UiButton>

        <button
          v-if="isLogin"
          class="user-info"
          type="button"
          @click="goToProfile"
        >
          <span class="avatar">
            <img
              v-if="avatarDisplayUrl"
              :src="avatarDisplayUrl"
              alt=""
              class="avatar-image"
            />
            <span v-else class="default-avatar">{{ usernameInitial }}</span>
          </span>
          <span class="user-copy">
            <strong>{{ username }}</strong>
            <span>个人资料</span>
          </span>
        </button>

        <button
          class="menu-toggle"
          type="button"
          :aria-expanded="mobileMenuOpen ? 'true' : 'false'"
          aria-controls="mobile-nav-drawer"
          :aria-label="mobileMenuOpen ? '关闭导航菜单' : '打开导航菜单'"
          @click="toggleMobileMenu"
        >
          <AppIcon
            :icon="mobileMenuOpen ? 'lucide:x' : 'lucide:menu'"
            class="menu-toggle-icon"
          />
        </button>
      </div>
    </div>

    <div
      v-if="mobileMenuOpen"
      class="mobile-nav-overlay"
      aria-hidden="true"
      @click="closeMobileMenu"
    ></div>

    <aside
      id="mobile-nav-drawer"
      class="mobile-nav-drawer"
      :class="{ 'mobile-nav-drawer--open': mobileMenuOpen }"
    >
      <div class="mobile-drawer-head">
        <strong class="mobile-drawer-title">导航</strong>
        <button
          class="mobile-close"
          type="button"
          aria-label="关闭导航菜单"
          @click="closeMobileMenu"
        >
          <AppIcon icon="lucide:x" class="mobile-close-icon" />
        </button>
      </div>

      <button
        v-if="isLogin"
        class="mobile-profile"
        type="button"
        @click="goToProfileFromMenu"
      >
        <span class="avatar">
          <img
            v-if="avatarDisplayUrl"
            :src="avatarDisplayUrl"
            alt=""
            class="avatar-image"
          />
          <span v-else class="default-avatar">{{ usernameInitial }}</span>
        </span>
        <span class="mobile-profile-copy">
          <strong>{{ username }}</strong>
          <span>个人资料</span>
        </span>
        <AppIcon icon="lucide:chevron-right" class="mobile-chevron" />
      </button>

      <UiButton
        v-else
        class="mobile-cta"
        as="button"
        variant="primary"
        leading-icon="lucide:log-in"
        @click="openLoginDialogFromMenu"
      >
        <span>登录 / 注册</span>
      </UiButton>

      <div class="mobile-nav-group">
        <p class="mobile-group-label">页面</p>
        <router-link
          v-for="item in mainNavItems"
          :key="`mobile-main-${item.key}`"
          v-bind="getNavLinkStateProps(item)"
          :to="item.to"
          class="mobile-nav-link"
          @click="closeMobileMenu"
        >
          <span class="mobile-link-main">
            <AppIcon :icon="item.icon" class="nav-link-icon" />
            <span>{{ item.label }}</span>
          </span>
          <AppIcon icon="lucide:chevron-right" class="mobile-chevron" />
        </router-link>
      </div>

      <div v-if="secondaryNavItems.length" class="mobile-nav-group">
        <p class="mobile-group-label">更多</p>
        <router-link
          v-for="item in secondaryNavItems"
          :key="`mobile-secondary-${item.key}`"
          v-bind="getNavLinkStateProps(item)"
          :to="item.to"
          class="mobile-nav-link mobile-nav-link--secondary"
          @click="closeMobileMenu"
        >
          <span class="mobile-link-main">
            <AppIcon :icon="item.icon" class="nav-link-icon" />
            <span>{{ item.label }}</span>
          </span>
          <AppIcon icon="lucide:chevron-right" class="mobile-chevron" />
        </router-link>
      </div>
    </aside>
  </nav>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { storeToRefs } from "pinia";
import { useUserStore } from "@/modules/account/stores/userStore";
import AppIcon from "@/shared/ui/branding/AppIcon.vue";
import BrandLogo from "@/shared/ui/branding/BrandLogo.vue";
import UiButton from "@/shared/ui/actions/UiButton.vue";
import { RouteLocation } from "@/app/router/route-names";
import { EXPLORE_NAV_ITEMS, WORKSPACE_NAV_ITEMS } from "@/app/shell/nav-items";
import { resolveShellContext } from "@/app/shell/shell-context";
import { getNavLinkStateProps } from "@/app/shell/nav-link-state";

const MOBILE_NAV_BREAKPOINT = 1024;
const SCROLL_THRESHOLD = 10;
const MOUSE_TOP_THRESHOLD = 10;

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();
const { avatarDisplayUrl, isLogin, username } = storeToRefs(userStore);

const isVisible = ref(true);
const mobileMenuOpen = ref(false);

const shellContext = computed(() =>
  resolveShellContext(route.name ? String(route.name) : undefined),
);

const mainNavItems = computed(() =>
  shellContext.value === "workspace"
    ? WORKSPACE_NAV_ITEMS.filter((item) => !item.requiresAuth || isLogin.value)
    : EXPLORE_NAV_ITEMS,
);

const secondaryNavItems = computed(() => {
  if (shellContext.value === "workspace") {
    return EXPLORE_NAV_ITEMS;
  }

  if (!isLogin.value) {
    return [];
  }

  return WORKSPACE_NAV_ITEMS.filter((item) => !item.requiresAuth || isLogin.value);
});

const usernameInitial = computed(() =>
  (username.value || "A").trim().charAt(0).toUpperCase() || "A",
);


const syncBodyScrollLock = () => {
  document.body.style.overflow =
    mobileMenuOpen.value && window.innerWidth <= MOBILE_NAV_BREAKPOINT
      ? "hidden"
      : "";
};

const closeMobileMenu = () => {
  mobileMenuOpen.value = false;
  syncBodyScrollLock();
};

const toggleMobileMenu = () => {
  mobileMenuOpen.value = !mobileMenuOpen.value;
  syncBodyScrollLock();
};

const goToProfile = () => {
  void router.push(RouteLocation.userProfile);
};

const goToProfileFromMenu = () => {
  closeMobileMenu();
  void router.push(RouteLocation.userProfile);
};

const openLoginDialog = () => {
  userStore.openLoginDialog();
};

const openLoginDialogFromMenu = () => {
  closeMobileMenu();
  userStore.openLoginDialog();
};

let lastScrollY = window.scrollY;
let ticking = false;

const handleScroll = () => {
  if (mobileMenuOpen.value) {
    isVisible.value = true;
    return;
  }

  const currentScrollY = window.scrollY;
  const scrollingDown =
    currentScrollY > lastScrollY && currentScrollY > SCROLL_THRESHOLD;
  const scrollingUp = currentScrollY < lastScrollY;

  if (scrollingDown) {
    isVisible.value = false;
  } else if (scrollingUp) {
    isVisible.value = true;
  }

  lastScrollY = currentScrollY;
};

const handleMouseMove = (event: MouseEvent) => {
  if (event.clientY <= MOUSE_TOP_THRESHOLD) {
    isVisible.value = true;
  }
};

const handleResize = () => {
  if (window.innerWidth > MOBILE_NAV_BREAKPOINT) {
    closeMobileMenu();
  } else {
    syncBodyScrollLock();
  }
};

const handleKeydown = (event: KeyboardEvent) => {
  if (event.key === "Escape") {
    closeMobileMenu();
  }
};

const onScroll = () => {
  if (ticking) {
    return;
  }

  window.requestAnimationFrame(() => {
    handleScroll();
    ticking = false;
  });

  ticking = true;
};

watch(
  () => route.fullPath,
  () => {
    closeMobileMenu();
    isVisible.value = true;
  },
);

onMounted(() => {
  window.addEventListener("scroll", onScroll);
  window.addEventListener("mousemove", handleMouseMove);
  window.addEventListener("resize", handleResize);
  window.addEventListener("keydown", handleKeydown);
  lastScrollY = window.scrollY;
  syncBodyScrollLock();
});

onUnmounted(() => {
  window.removeEventListener("scroll", onScroll);
  window.removeEventListener("mousemove", handleMouseMove);
  window.removeEventListener("resize", handleResize);
  window.removeEventListener("keydown", handleKeydown);
  document.body.style.overflow = "";
});
</script>

<style scoped lang="scss">
.navbar {
  position: fixed;
  inset: 0 0 auto;
  z-index: var(--z-nav);
  border-bottom: 1px solid rgba(255, 255, 255, 0.44);
  transition:
    transform var(--duration-base) var(--ease-standard),
    background var(--duration-base) var(--ease-standard),
    box-shadow var(--duration-base) var(--ease-standard);
}

.navbar.hidden {
  transform: translateY(-100%);
}

.navbar--public {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.9), rgba(255, 255, 255, 0.78));
  box-shadow:
    0 18px 36px -30px rgba(79, 70, 229, 0.24),
    inset 0 -1px 0 rgba(255, 255, 255, 0.58);
}

.navbar--workspace {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.9), rgba(255, 255, 255, 0.8));
  box-shadow:
    0 16px 30px -28px rgba(15, 23, 42, 0.16),
    inset 0 -1px 0 rgba(255, 255, 255, 0.58);
}

.nav-container {
  max-width: min(1440px, 100vw);
  min-height: var(--nav-height);
  margin: 0 auto;
  padding: 0 1.25rem;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto auto;
  align-items: center;
  gap: 1.1rem;
}

.brand-cluster {
  display: flex;
  align-items: center;
  gap: 0.9rem;
  min-width: 0;
}

.brand-mark {
  width: 2.9rem;
  height: 2.9rem;
  border-radius: 999px;
  padding: 0.4rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.96), rgba(255, 255, 255, 0.82));
  box-shadow: 0 18px 30px -24px rgba(79, 70, 229, 0.24);
}

.brand-logo {
  width: 100%;
  height: 100%;
}

.brand-title {
  color: var(--color-text-dark);
  text-decoration: none;
  font-size: 1.02rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  white-space: nowrap;
}

.nav-links {
  display: flex;
  align-items: center;
  min-width: 0;
  padding: 0.32rem 0.5rem;
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: var(--radius-pill-40);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.86), rgba(255, 255, 255, 0.72));
  box-shadow: 0 16px 30px -28px rgba(15, 23, 42, 0.14);
}

.nav-links--primary {
  justify-content: center;
  gap: 0.4rem;
  min-height: 3.5rem;
}

.nav-links--secondary {
  gap: 0.35rem;
  justify-content: flex-end;
  min-height: 3.3rem;
}

.nav-link {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.7rem 0.96rem;
  border-radius: var(--radius-pill);
  color: #334155;
  text-decoration: none;
  border: 1px solid transparent;
  font-size: 0.92rem;
  font-weight: 600;
  transition:
    transform var(--duration-fast) var(--ease-standard),
    color var(--duration-fast) var(--ease-standard),
    border-color var(--duration-fast) var(--ease-standard),
    background var(--duration-fast) var(--ease-standard),
    box-shadow var(--duration-fast) var(--ease-standard);
}

.nav-link:hover {
  transform: translateY(-1px);
  color: var(--color-primary);
  background: rgba(255, 255, 255, 0.7);
  border-color: rgba(99, 102, 241, 0.14);
}

.nav-link.active {
  color: var(--color-primary);
  background: linear-gradient(135deg, rgba(219, 234, 254, 0.74), rgba(237, 233, 254, 0.7));
  border-color: rgba(99, 102, 241, 0.18);
  box-shadow: 0 14px 28px -28px rgba(79, 70, 229, 0.5);
}

.nav-link--secondary {
  padding-inline: 0.82rem;
  background: rgba(255, 255, 255, 0.5);
  font-size: 0.86rem;
}

.nav-link--with-icon {
  gap: 0.45rem;
}

.nav-link-icon {
  width: 1rem;
  height: 1rem;
  flex-shrink: 0;
}

.nav-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  justify-self: end;
}

.cta-btn {
  white-space: nowrap;
}

.menu-toggle {
  display: none;
  width: 2.8rem;
  height: 2.8rem;
  border: 1px solid rgba(148, 163, 184, 0.22);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.84);
  color: var(--color-text-dark);
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: var(--shadow-control);
}

.menu-toggle-icon,
.mobile-close-icon {
  width: 1.15rem;
  height: 1.15rem;
}

.user-info {
  min-width: 0;
  max-width: 15rem;
  display: inline-flex;
  align-items: center;
  gap: 0.7rem;
  padding: 0.4rem 0.5rem;
  border-radius: 999px;
  border: 1px solid rgba(148, 163, 184, 0.16);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.88), rgba(255, 255, 255, 0.76));
  cursor: pointer;
  box-shadow: 0 16px 30px -26px rgba(15, 23, 42, 0.16);
  transition:
    transform var(--duration-fast) var(--ease-standard),
    border-color var(--duration-fast) var(--ease-standard),
    background var(--duration-fast) var(--ease-standard);
}

.user-info:hover {
  transform: translateY(-1px);
  border-color: rgba(99, 102, 241, 0.26);
  background: rgba(255, 255, 255, 0.94);
}

.avatar {
  width: 2.45rem;
  height: 2.45rem;
  border-radius: 999px;
  overflow: hidden;
  background: var(--grad-primary);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  font-weight: 700;
  flex-shrink: 0;
  box-shadow: 0 16px 24px -18px rgba(79, 70, 229, 0.58);
}

.default-avatar {
  width: 100%;
  height: 100%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  text-transform: uppercase;
  font-size: 0.98rem;
}

.avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.user-copy {
  min-width: 0;
  display: flex;
  flex-direction: column;
  text-align: left;
}

.user-copy strong,
.user-copy span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-copy strong {
  color: var(--color-text-dark);
  font-size: 0.92rem;
}

.user-copy span {
  color: var(--color-text-subtle);
  font-size: 0.76rem;
}

.mobile-nav-overlay {
  position: fixed;
  inset: var(--nav-height) 0 0;
  background: rgba(15, 23, 42, 0.24);
  backdrop-filter: blur(4px);
}

.mobile-nav-drawer {
  position: fixed;
  top: var(--nav-height);
  right: 0;
  width: min(90vw, 390px);
  height: calc(100vh - var(--nav-height));
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  overflow-y: auto;
  border-left: 1px solid rgba(148, 163, 184, 0.18);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(244, 247, 255, 0.98));
  box-shadow: -18px 0 40px rgba(15, 23, 42, 0.18);
  transform: translateX(100%);
  transition: transform var(--duration-base) var(--ease-standard);
}

.mobile-nav-drawer--open {
  transform: translateX(0);
}

.mobile-drawer-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.mobile-drawer-title {
  color: var(--color-text-dark);
  font-size: 1rem;
}

.mobile-close {
  width: 2.35rem;
  height: 2.35rem;
  border-radius: 999px;
  border: 1px solid rgba(148, 163, 184, 0.2);
  background: #ffffff;
  color: var(--color-text-dark);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.mobile-profile {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  width: 100%;
  padding: 0.95rem 1rem;
  border: 1px solid rgba(99, 102, 241, 0.16);
  border-radius: 1.3rem;
  background: linear-gradient(135deg, rgba(219, 234, 254, 0.84), rgba(255, 255, 255, 0.96));
  color: var(--color-text-dark);
  text-align: left;
  cursor: pointer;
}

.mobile-cta {
  width: 100%;
}

.mobile-profile-copy {
  display: flex;
  flex: 1;
  min-width: 0;
  flex-direction: column;
  gap: 0.2rem;
}

.mobile-profile-copy strong,
.mobile-profile-copy span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mobile-profile-copy span {
  font-size: 0.88rem;
  color: var(--color-text-muted);
}

.mobile-nav-group {
  display: flex;
  flex-direction: column;
  gap: 0.55rem;
}

.mobile-group-label {
  margin: 0;
  color: #6366f1;
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.mobile-nav-link {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.95rem 1rem;
  border-radius: 1.1rem;
  border: 1px solid transparent;
  background: rgba(255, 255, 255, 0.92);
  color: #334155;
  text-decoration: none;
  transition:
    transform var(--duration-fast) var(--ease-standard),
    border-color var(--duration-fast) var(--ease-standard),
    background var(--duration-fast) var(--ease-standard);
}

.mobile-nav-link.active {
  color: var(--color-primary);
  border-color: rgba(99, 102, 241, 0.18);
  background: linear-gradient(135deg, rgba(219, 234, 254, 0.8), rgba(255, 255, 255, 0.98));
}

.mobile-nav-link--secondary {
  background: rgba(248, 250, 252, 0.9);
}

.mobile-link-main {
  display: inline-flex;
  align-items: center;
  gap: 0.7rem;
}

.mobile-chevron {
  width: 1rem;
  height: 1rem;
  color: #94a3b8;
  flex-shrink: 0;
}

@media (max-width: 1340px) {
  .nav-container {
    grid-template-columns: auto minmax(0, 1fr) auto;
  }

  .nav-links--secondary {
    display: none;
  }
}

@media (max-width: 1180px) {
  .brand-title {
    font-size: 1rem;
  }

  .nav-link {
    padding: 0.62rem 0.8rem;
    font-size: 0.88rem;
  }

  .user-info {
    max-width: 13.2rem;
  }
}

@media (max-width: 1024px) {
  .nav-container {
    display: flex;
    gap: 0.75rem;
    padding: 0 0.95rem;
  }

  .nav-links,
  .cta-btn,
  .user-info {
    display: none;
  }

  .menu-toggle {
    display: inline-flex;
    margin-left: auto;
  }

}

@media (max-width: 640px) {
  .nav-container {
    padding: 0 0.9rem;
  }

  .brand-mark {
    width: 2.72rem;
    height: 2.72rem;
  }

  .brand-title {
    max-width: 10ch;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .mobile-nav-drawer {
    width: 100%;
    max-width: none;
  }
}
</style>
