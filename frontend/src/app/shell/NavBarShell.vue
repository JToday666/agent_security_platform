<template>
  <nav class="navbar" :class="{ hidden: !isVisible && !mobileMenuOpen }">
    <div class="nav-container">
      <div class="brand-cluster">
        <router-link
          :to="RouteLocation.home"
          class="brand-mark"
          aria-label="返回首页"
        >
          <BrandLogo
            class="brand-logo"
            alt="智能体安全评测平台标志"
            :priority="true"
          />
        </router-link>
        <router-link :to="RouteLocation.home" class="brand-title">
          智能体安全评测平台
        </router-link>
      </div>

      <div class="nav-links">
        <router-link
          v-for="item in visibleNavItems"
          :key="`desktop-${item.key}`"
          v-bind="getLinkStateProps(item)"
          :to="item.to"
          class="nav-link"
        >
          <AppIcon :icon="item.icon" class="nav-link-icon" />
          <span>{{ item.label }}</span>
        </router-link>
      </div>

      <div class="nav-actions">
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

        <button
          v-if="isLogin"
          class="user-info"
          type="button"
          title="查看个人资料"
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
          <span class="username">{{ username }}</span>
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
        <strong class="mobile-drawer-title">导航菜单</strong>
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
          <span>查看个人资料</span>
        </span>
        <AppIcon icon="lucide:chevron-right" class="mobile-chevron" />
      </button>

      <div class="mobile-nav-group">
        <router-link
          v-for="item in visibleNavItems"
          :key="`mobile-${item.key}`"
          v-bind="getLinkStateProps(item)"
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
    </aside>
  </nav>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { useRoute, useRouter, type RouteLocationRaw } from "vue-router";
import { useUserStore } from "@/modules/account/stores/UserStore";
import { storeToRefs } from "pinia";
import AppIcon from "@/shared/ui/AppIcon.vue";
import BrandLogo from "@/shared/ui/BrandLogo.vue";
import { RouteLocation } from "@/app/router/RouteNames";

interface NavItem {
  key: string;
  label: string;
  icon: string;
  to: RouteLocationRaw;
  requiresAuth?: boolean;
  exact?: boolean;
}

const MOBILE_NAV_BREAKPOINT = 1024;
const SCROLL_THRESHOLD = 10;
const MOUSE_TOP_THRESHOLD = 10;

const NAV_ITEMS: NavItem[] = [
  {
    key: "home",
    label: "首页",
    icon: "lucide:house",
    to: RouteLocation.home,
    exact: true,
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
    key: "records",
    label: "评测记录",
    icon: "lucide:clipboard-list",
    to: RouteLocation.userCenter,
    requiresAuth: true,
  },
  {
    key: "submit",
    label: "提交测评",
    icon: "lucide:file-plus-2",
    to: RouteLocation.agentSubmit,
    requiresAuth: true,
  },
  {
    key: "contact",
    label: "联系我们",
    icon: "lucide:mail",
    to: RouteLocation.contact,
  },
];

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();
const { avatarDisplayUrl, isLogin, username } = storeToRefs(userStore);

const isVisible = ref(true);
const mobileMenuOpen = ref(false);

const visibleNavItems = computed(() =>
  NAV_ITEMS.filter((item) => !item.requiresAuth || isLogin.value),
);

const usernameInitial = computed(() =>
  (username.value || "A").trim().charAt(0).toUpperCase() || "A",
);

const getLinkStateProps = (item: NavItem) =>
  item.exact ? { exactActiveClass: "active" } : { activeClass: "active" };

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

<style scoped>
.navbar {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  z-index: var(--z-nav);
  border-bottom: 1px solid rgba(226, 232, 240, 0.88);
  background:
    linear-gradient(180deg, rgba(248, 250, 252, 0.92), rgba(255, 255, 255, 0.82));
  box-shadow:
    0 16px 32px -28px rgba(15, 23, 42, 0.36),
    0 0 0 1px rgba(255, 255, 255, 0.78) inset;
  transition: transform 0.35s ease;
  transform: translateY(0);
}

.navbar.hidden {
  transform: translateY(-100%);
}

.nav-container {
  position: relative;
  z-index: 2;
  width: 100%;
  padding: 0 clamp(1.25rem, 1.8vw, 1.75rem);
  height: var(--nav-height);
  display: grid;
  grid-template-columns: max-content minmax(0, 1fr) max-content;
  align-items: center;
  column-gap: clamp(0.9rem, 1.4vw, 1.25rem);
}

.brand-cluster {
  display: flex;
  align-items: center;
  gap: 0.9rem;
  min-width: 0;
  flex-shrink: 0;
}

.brand-mark {
  width: 2.72rem;
  height: 2.72rem;
  border-radius: 0.9rem;
  overflow: hidden;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  text-decoration: none;
  flex-shrink: 0;
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease,
    background 0.2s ease;
}

.brand-mark:hover {
  transform: translateY(-1px);
  box-shadow: 0 16px 28px -22px rgba(37, 99, 235, 0.42);
}

.brand-mark:focus-visible,
.brand-title:focus-visible {
  outline: none;
  box-shadow: var(--shadow-focus-accent);
}

.brand-logo {
  width: 100%;
  height: 100%;
}

.brand-title {
  color: #0f172a;
  display: inline-flex;
  align-items: center;
  text-decoration: none;
  font-size: 1.18rem;
  font-weight: 900;
  letter-spacing: -0.03em;
  line-height: 1;
  white-space: nowrap;
  transition:
    transform 0.2s ease,
    filter 0.2s ease;
}

@supports ((-webkit-background-clip: text) or (background-clip: text)) {
  .brand-title {
    background: linear-gradient(120deg, #0f172a 0%, #2563eb 52%, #06b6d4 100%);
    background-clip: text;
    -webkit-background-clip: text;
    color: transparent;
    -webkit-text-fill-color: transparent;
  }
}

.brand-title:hover {
  transform: translateY(-1px);
  filter: brightness(1.04);
}

.nav-links {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.52rem;
  min-width: 0;
  width: 100%;
  padding-left: clamp(1.75rem, 5vw, 5.75rem);
}

.nav-link {
  display: inline-flex;
  align-items: center;
  gap: 0.55rem;
  padding: 0.68rem 0.92rem;
  border-radius: 999px;
  border: 1px solid transparent;
  color: #334155;
  text-decoration: none;
  font-size: 0.95rem;
  font-weight: 600;
  white-space: nowrap;
  transition:
    color 0.2s ease,
    transform 0.2s ease,
    border-color 0.2s ease,
    background 0.2s ease,
    box-shadow 0.2s ease;
}

.nav-link-icon {
  width: 1rem;
  height: 1rem;
  flex-shrink: 0;
}

.nav-link:hover {
  color: #0f172a;
  transform: translateY(-1px);
  border-color: rgba(226, 232, 240, 0.92);
  background: rgba(255, 255, 255, 0.88);
  box-shadow: 0 12px 24px -24px rgba(15, 23, 42, 0.32);
}

.nav-link.active {
  color: #1d4ed8;
  border-color: rgba(96, 165, 250, 0.34);
  background:
    linear-gradient(135deg, rgba(219, 234, 254, 0.88), rgba(255, 255, 255, 0.98));
  box-shadow: 0 14px 28px -24px rgba(37, 99, 235, 0.4);
}

.nav-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-shrink: 0;
  min-width: 0;
  justify-self: end;
}

.menu-toggle {
  display: none;
  width: 2.7rem;
  height: 2.7rem;
  border-radius: 999px;
  border: 1px solid rgba(203, 213, 225, 0.88);
  background: rgba(255, 255, 255, 0.88);
  color: #0f172a;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 10px 22px -18px rgba(15, 23, 42, 0.32);
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
  padding: 0.34rem 0.48rem 0.34rem 0.34rem;
  border-radius: 999px;
  border: 1px solid rgba(226, 232, 240, 0.96);
  background: rgba(255, 255, 255, 0.88);
  cursor: pointer;
  box-shadow: 0 14px 28px -24px rgba(15, 23, 42, 0.34);
  transition:
    transform 0.2s ease,
    border-color 0.2s ease,
    background 0.2s ease;
}

.user-info:hover {
  transform: translateY(-1px);
  border-color: rgba(96, 165, 250, 0.28);
  background: #ffffff;
}

.avatar {
  width: 2.3rem;
  height: 2.3rem;
  border-radius: 999px;
  overflow: hidden;
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  font-weight: 700;
  flex-shrink: 0;
  box-shadow: 0 10px 20px -14px rgba(37, 99, 235, 0.5);
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
  display: block;
  object-fit: cover;
}

.username {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #0f172a;
  font-size: 0.94rem;
  font-weight: 600;
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
  width: min(88vw, 360px);
  height: calc(100vh - var(--nav-height));
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  overflow-y: auto;
  border-left: 1px solid rgba(226, 232, 240, 0.9);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.98));
  box-shadow: -14px 0 34px rgba(15, 23, 42, 0.16);
  transform: translateX(100%);
  transition: transform 0.24s ease;
}

.mobile-nav-drawer--open {
  transform: translateX(0);
}

.mobile-drawer-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.mobile-drawer-title {
  color: #0f172a;
  font-size: 1rem;
}

.mobile-close {
  width: 2.35rem;
  height: 2.35rem;
  border-radius: 999px;
  border: 1px solid rgba(226, 232, 240, 0.96);
  background: #ffffff;
  color: #0f172a;
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
  border: 1px solid rgba(191, 219, 254, 0.72);
  border-radius: 1.25rem;
  background:
    linear-gradient(135deg, rgba(219, 234, 254, 0.84), rgba(255, 255, 255, 0.96));
  color: #0f172a;
  text-align: left;
  cursor: pointer;
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
  color: #475569;
}

.mobile-nav-group {
  display: flex;
  flex-direction: column;
  gap: 0.55rem;
}

.mobile-nav-link {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.95rem 1rem;
  border-radius: 1.1rem;
  border: 1px solid transparent;
  background: rgba(255, 255, 255, 0.9);
  color: #334155;
  text-decoration: none;
  transition:
    transform 0.2s ease,
    border-color 0.2s ease,
    background 0.2s ease;
}

.mobile-nav-link.active {
  color: #1d4ed8;
  border-color: rgba(96, 165, 250, 0.24);
  background:
    linear-gradient(135deg, rgba(219, 234, 254, 0.8), rgba(255, 255, 255, 0.98));
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
  .brand-title {
    font-size: 1.1rem;
  }

  .nav-links {
    padding-left: clamp(1rem, 2.8vw, 2.8rem);
  }
}

@media (max-width: 1180px) {
  .nav-container {
    padding: 0 1rem;
  }

  .brand-cluster {
    gap: 0.72rem;
  }

  .brand-title {
    font-size: 1rem;
  }

  .nav-links {
    gap: 0.34rem;
    padding-left: 0.8rem;
  }

  .nav-link {
    gap: 0.48rem;
    padding: 0.6rem 0.68rem;
    font-size: 0.89rem;
  }

  .user-info {
    max-width: 13rem;
  }
}

@media (max-width: 1024px) {
  .nav-container {
    display: flex;
    gap: 0.75rem;
    padding: 0 0.95rem;
  }

  .nav-links,
  .user-info {
    display: none;
  }

  .menu-toggle {
    display: inline-flex;
  }

  .nav-actions {
    margin-left: auto;
  }

  .brand-title {
    max-width: 12ch;
    overflow: hidden;
    text-overflow: ellipsis;
  }
}

@media (max-width: 640px) {
  .nav-container {
    padding: 0 0.9rem;
  }

  .brand-mark {
    width: 2.45rem;
    height: 2.45rem;
  }

  .brand-title {
    max-width: 9ch;
    font-size: 0.98rem;
  }

  .mobile-nav-drawer {
    width: 100%;
    max-width: none;
  }
}
</style>
