<template>
  <nav class="navbar" :class="{ hidden: !isVisible && !mobileMenuOpen }">
    <div class="nav-container">
      <router-link :to="RouteLocation.home" class="logo">
        智能体安全评测平台
      </router-link>

      <div class="right-section">
        <div class="nav-links">
          <router-link :to="RouteLocation.home" class="nav-link" exact-active-class="active">
            <AppIcon icon="lucide:house" class="nav-link-icon" />
            <span>首页</span>
          </router-link>
          <router-link :to="RouteLocation.datasetList" class="nav-link" active-class="active">
            <AppIcon icon="lucide:database" class="nav-link-icon" />
            <span>评测目录</span>
          </router-link>
          <router-link :to="RouteLocation.leaderboard" class="nav-link" active-class="active">
            <AppIcon icon="lucide:trophy" class="nav-link-icon" />
            <span>排行榜</span>
          </router-link>
          <router-link :to="RouteLocation.contact" class="nav-link" active-class="active">
            <AppIcon icon="lucide:mail" class="nav-link-icon" />
            <span>联系我们</span>
          </router-link>
          <router-link
            v-if="isLogin"
            :to="RouteLocation.userCenter"
            class="nav-link"
            active-class="active"
          >
            <AppIcon icon="lucide:layout-dashboard" class="nav-link-icon" />
            <span>用户中心</span>
          </router-link>
        </div>

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

        <div
          v-if="isLogin"
          class="user-info"
          title="查看个人资料"
          @click="goToProfile"
        >
          <div class="avatar">
            <span class="default-avatar">{{ usernameInitial }}</span>
          </div>
          <span class="username">{{ username }}</span>
        </div>
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
          <span class="default-avatar">{{ usernameInitial }}</span>
        </span>
        <span class="mobile-profile-copy">
          <strong>{{ username }}</strong>
          <span>查看个人资料</span>
        </span>
        <AppIcon icon="lucide:chevron-right" class="mobile-chevron" />
      </button>

      <div class="mobile-nav-group">
        <router-link
          :to="RouteLocation.home"
          class="mobile-nav-link"
          exact-active-class="active"
          @click="closeMobileMenu"
        >
          <span class="mobile-link-main">
            <AppIcon icon="lucide:house" class="nav-link-icon" />
            <span>首页</span>
          </span>
          <AppIcon icon="lucide:chevron-right" class="mobile-chevron" />
        </router-link>
        <router-link
          :to="RouteLocation.datasetList"
          class="mobile-nav-link"
          active-class="active"
          @click="closeMobileMenu"
        >
          <span class="mobile-link-main">
            <AppIcon icon="lucide:database" class="nav-link-icon" />
            <span>评测目录</span>
          </span>
          <AppIcon icon="lucide:chevron-right" class="mobile-chevron" />
        </router-link>
        <router-link
          :to="RouteLocation.leaderboard"
          class="mobile-nav-link"
          active-class="active"
          @click="closeMobileMenu"
        >
          <span class="mobile-link-main">
            <AppIcon icon="lucide:trophy" class="nav-link-icon" />
            <span>排行榜</span>
          </span>
          <AppIcon icon="lucide:chevron-right" class="mobile-chevron" />
        </router-link>
        <router-link
          :to="RouteLocation.contact"
          class="mobile-nav-link"
          active-class="active"
          @click="closeMobileMenu"
        >
          <span class="mobile-link-main">
            <AppIcon icon="lucide:mail" class="nav-link-icon" />
            <span>联系我们</span>
          </span>
          <AppIcon icon="lucide:chevron-right" class="mobile-chevron" />
        </router-link>
        <template v-if="isLogin">
          <router-link
            :to="RouteLocation.userCenter"
            class="mobile-nav-link"
            active-class="active"
            @click="closeMobileMenu"
          >
            <span class="mobile-link-main">
              <AppIcon icon="lucide:clipboard-list" class="nav-link-icon" />
              <span>评测记录</span>
            </span>
            <AppIcon icon="lucide:chevron-right" class="mobile-chevron" />
          </router-link>
          <router-link
            :to="RouteLocation.agentSubmit"
            class="mobile-nav-link"
            active-class="active"
            @click="closeMobileMenu"
          >
            <span class="mobile-link-main">
              <AppIcon icon="lucide:bot" class="nav-link-icon" />
              <span>提交智能体</span>
            </span>
            <AppIcon icon="lucide:chevron-right" class="mobile-chevron" />
          </router-link>
          <router-link
            :to="RouteLocation.userProfile"
            class="mobile-nav-link"
            active-class="active"
            @click="closeMobileMenu"
          >
            <span class="mobile-link-main">
              <AppIcon icon="lucide:square-pen" class="nav-link-icon" />
              <span>个人资料</span>
            </span>
            <AppIcon icon="lucide:chevron-right" class="mobile-chevron" />
          </router-link>
        </template>
      </div>
    </aside>
  </nav>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useUserStore } from "@/modules/account/stores/UserStore";
import { storeToRefs } from "pinia";
import AppIcon from "@/shared/ui/AppIcon.vue";
import { RouteLocation } from "@/app/router/RouteNames";

const MOBILE_NAV_BREAKPOINT = 1024;

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();
const { isLogin, username } = storeToRefs(userStore);

const isVisible = ref(true);
const mobileMenuOpen = ref(false);

const usernameInitial = computed(() =>
  (username.value || "A").trim().charAt(0).toUpperCase() || "A",
);

const syncBodyScrollLock = () => {
  document.body.style.overflow =
    mobileMenuOpen.value && window.innerWidth <= MOBILE_NAV_BREAKPOINT ? "hidden" : "";
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
const SCROLL_THRESHOLD = 10;
const MOUSE_TOP_THRESHOLD = 10;

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

let ticking = false;
const onScroll = () => {
  if (!ticking) {
    window.requestAnimationFrame(() => {
      handleScroll();
      ticking = false;
    });
    ticking = true;
  }
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
  box-shadow:
    0 4px 20px rgba(0, 0, 0, 0.05),
    0 0 0 1px rgba(255, 255, 255, 0.8) inset;
  z-index: var(--z-nav);
  transition: transform 0.35s ease;
  transform: translateY(0);
}

.navbar.hidden {
  transform: translateY(-100%);
}

.nav-container {
  position: relative;
  z-index: 2;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 2rem;
  height: var(--nav-height);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.logo {
  font-size: 1.6rem;
  font-weight: 800;
  background: linear-gradient(135deg, #2563eb, #7c3aed);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  text-decoration: none;
  letter-spacing: -0.03em;
  transition: opacity 0.2s ease;
}

.logo:hover {
  opacity: 0.82;
}

.right-section {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.nav-links {
  display: flex;
  gap: 1.5rem;
  align-items: center;
}

.nav-link {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  color: #334155;
  text-decoration: none;
  font-weight: 500;
  font-size: 0.98rem;
  padding: 0.5rem 0;
  position: relative;
  transition: color 0.2s ease;
}

.nav-link-icon {
  width: 1rem;
  height: 1rem;
  flex-shrink: 0;
}

.nav-link::after {
  content: "";
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 0;
  height: 2px;
  background: linear-gradient(90deg, #2563eb, #7c3aed);
  transition: width 0.2s ease;
}

.nav-link:hover,
.nav-link.active {
  color: #2563eb;
}

.nav-link:hover::after,
.nav-link.active::after {
  width: 100%;
}

.menu-toggle {
  display: none;
  align-items: center;
  justify-content: center;
  width: 2.9rem;
  height: 2.9rem;
  border: 1px solid rgba(148, 163, 184, 0.28);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.72);
  color: #0f172a;
  backdrop-filter: blur(10px);
}

.menu-toggle-icon,
.mobile-close-icon {
  width: 1.2rem;
  height: 1.2rem;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  cursor: pointer;
  padding: 0.3rem 0.8rem 0.3rem 0.4rem;
  border-radius: 40px;
  background: rgba(255, 255, 255, 0.3);
  transition:
    background 0.2s ease,
    box-shadow 0.2s ease;
  border: 1px solid rgba(255, 255, 255, 0.5);
}

.user-info:hover {
  background: rgba(255, 255, 255, 0.5);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  overflow: hidden;
  background: linear-gradient(135deg, #2563eb, #7c3aed);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  font-weight: 700;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.26);
  flex-shrink: 0;
}

.default-avatar {
  width: 100%;
  height: 100%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  text-transform: uppercase;
  font-size: 1.05rem;
}

.username {
  font-size: 0.95rem;
  font-weight: 500;
  color: #1e293b;
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.97), rgba(248, 250, 252, 0.98));
  border-left: 1px solid rgba(226, 232, 240, 0.85);
  box-shadow: -12px 0 36px rgba(15, 23, 42, 0.16);
  transform: translateX(100%);
  transition: transform 0.24s ease;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  overflow-y: auto;
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
  width: 2.4rem;
  height: 2.4rem;
  border: 1px solid #e2e8f0;
  border-radius: 999px;
  background: #ffffff;
  color: #0f172a;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.mobile-profile {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  width: 100%;
  padding: 0.95rem 1rem;
  border: 1px solid rgba(191, 219, 254, 0.7);
  border-radius: 1.25rem;
  background: linear-gradient(135deg, rgba(219, 234, 254, 0.82), rgba(237, 233, 254, 0.72));
  color: #0f172a;
  text-align: left;
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
  color: #334155;
  text-decoration: none;
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid transparent;
  transition:
    transform 0.2s ease,
    border-color 0.2s ease,
    background 0.2s ease;
}

.mobile-nav-link.active {
  color: #2563eb;
  border-color: rgba(59, 130, 246, 0.18);
  background: linear-gradient(135deg, rgba(219, 234, 254, 0.72), rgba(255, 255, 255, 0.96));
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

@media (max-width: 1024px) {
  .nav-container {
    padding: 0 1rem;
  }

  .nav-links,
  .user-info {
    display: none;
  }

  .menu-toggle {
    display: inline-flex;
  }

  .logo {
    font-size: 1.45rem;
  }
}

@media (max-width: 640px) {
  .logo {
    max-width: 14ch;
    font-size: 1.2rem;
    line-height: 1.15;
  }

  .mobile-nav-drawer {
    width: 100%;
    max-width: none;
  }
}
</style>