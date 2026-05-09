<template>
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
        <span class="brand-title-prefix">AEGIS </span>
        <span>智能体安全评测平台</span>
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
        @click="$emit('open-login')"
      >
        <span>登录 / 注册</span>
      </UiButton>

      <UserNavMenu
        v-if="isLogin"
        :avatar-display-url="avatarDisplayUrl"
        :has-avatar-error="hasAvatarError"
        :username="username"
        :username-initial="usernameInitial"
        @profile="$emit('profile')"
        @avatar-error="$emit('avatar-error')"
      />
    </div>

    <div class="nav-menu-zone">
      <button
        class="menu-toggle"
        type="button"
        :aria-expanded="mobileMenuOpen ? 'true' : 'false'"
        aria-controls="mobile-nav-drawer"
        :aria-label="mobileMenuOpen ? '关闭导航菜单' : '打开导航菜单'"
        @click="$emit('toggle-mobile-menu')"
      >
        <AppIcon
          :icon="mobileMenuOpen ? 'lucide:x' : 'lucide:menu'"
          class="menu-toggle-icon"
        />
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { RouteLocation } from "@/app/router/route-names";
import { getNavLinkStateProps } from "@/app/shell/nav-link-state";
import type { AppNavItem } from "@/app/shell/nav-items";
import type { ShellContext } from "@/app/shell/shell-context";
import UserNavMenu from "@/app/shell/UserNavMenu.vue";
import UiButton from "@/shared/ui/actions/UiButton.vue";
import AppIcon from "@/shared/ui/branding/AppIcon.vue";
import BrandLogo from "@/shared/ui/branding/BrandLogo.vue";

defineProps<{
  avatarDisplayUrl: string;
  hasAvatarError: boolean;
  isLogin: boolean;
  mainNavItems: AppNavItem[];
  mobileMenuOpen: boolean;
  secondaryNavItems: AppNavItem[];
  shellContext: ShellContext;
  username: string;
  usernameInitial: string;
}>();

defineEmits<{
  (event: "avatar-error"): void;
  (event: "open-login"): void;
  (event: "profile"): void;
  (event: "toggle-mobile-menu"): void;
}>();
</script>

<style scoped lang="scss">
$NAV_BREAKPOINT_TABLET: 1120px;

.nav-container {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto auto;
  align-items: center;
  gap: 0.9rem;
  max-width: min(1440px, 100vw);
  min-height: var(--nav-height);
  margin: 0 auto;
  padding: 0 1.1rem;
}

.brand-cluster {
  display: flex;
  align-items: center;
  gap: 0.72rem;
  min-width: 0;
}

.brand-mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.45rem;
  height: 2.45rem;
  padding: 0.32rem;
  border-radius: 999px;
  background: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.96),
    rgba(255, 255, 255, 0.82)
  );
  box-shadow: 0 18px 30px -24px rgba(79, 70, 229, 0.24);
}

.brand-logo {
  width: 100%;
  height: 100%;
}

.brand-title {
  color: var(--color-text-dark);
  font-size: 0.98rem;
  font-weight: 800;
  letter-spacing: 0;
  text-decoration: none;
  white-space: nowrap;
}

.nav-links {
  display: flex;
  align-items: center;
  min-width: 0;
  padding: 0.22rem 0.36rem;
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: var(--radius-pill-40);
  background: linear-gradient(
    180deg,
    rgba(255, 255, 255, 0.86),
    rgba(255, 255, 255, 0.72)
  );
  box-shadow: 0 16px 30px -28px rgba(15, 23, 42, 0.14);
}

.nav-links--primary {
  justify-content: center;
  gap: 0.28rem;
  min-height: 2.85rem;
}

.nav-links--secondary {
  justify-content: flex-end;
  gap: 0.24rem;
  min-height: 2.75rem;
}

.nav-link {
  display: inline-flex;
  align-items: center;
  gap: 0.42rem;
  padding: 0.52rem 0.78rem;
  border: 1px solid transparent;
  border-radius: var(--radius-pill);
  color: #334155;
  font-size: 0.9rem;
  font-weight: 600;
  text-decoration: none;
  transition:
    transform var(--duration-fast) var(--ease-standard),
    color var(--duration-fast) var(--ease-standard),
    border-color var(--duration-fast) var(--ease-standard),
    background var(--duration-fast) var(--ease-standard),
    box-shadow var(--duration-fast) var(--ease-standard);
  white-space: nowrap;
}

.nav-link:hover {
  border-color: rgba(99, 102, 241, 0.14);
  background: rgba(255, 255, 255, 0.7);
  color: var(--color-primary);
  transform: translateY(-1px);
}

.nav-link.active {
  border-color: rgba(99, 102, 241, 0.18);
  background: linear-gradient(
    135deg,
    rgba(219, 234, 254, 0.74),
    rgba(237, 233, 254, 0.7)
  );
  box-shadow: 0 14px 28px -28px rgba(79, 70, 229, 0.5);
  color: var(--color-primary);
}

.nav-link--secondary {
  padding-inline: 0.68rem;
  background: rgba(255, 255, 255, 0.5);
  font-size: 0.84rem;
}

.nav-link--with-icon {
  gap: 0.45rem;
}

.nav-link-icon {
  flex-shrink: 0;
  width: 1rem;
  height: 1rem;
}

.nav-actions {
  display: flex;
  align-items: center;
  justify-self: end;
  gap: 0.6rem;
}

.nav-menu-zone {
  display: flex;
  align-items: center;
  justify-self: end;
  margin-left: auto;
}

.cta-btn {
  white-space: nowrap;
}

.menu-toggle {
  display: none;
  align-items: center;
  justify-content: center;
  width: 2.55rem;
  height: 2.55rem;
  border: 1px solid rgba(148, 163, 184, 0.22);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.84);
  box-shadow: var(--shadow-control);
  color: var(--color-text-dark);
  cursor: pointer;
}

.menu-toggle-icon {
  width: 1.15rem;
  height: 1.15rem;
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
    font-size: 0.94rem;
  }

  .nav-links {
    gap: 0.2rem;
  }

  .nav-link {
    padding: 0.45rem 0.56rem;
    font-size: 0.86rem;
  }
}

@media (max-width: $NAV_BREAKPOINT_TABLET) {
  .nav-container {
    display: flex;
    gap: 0.65rem;
    padding: 0 0.95rem;
  }

  .nav-links,
  .nav-actions {
    display: none;
  }

  .menu-toggle {
    display: inline-flex;
  }
}

@media (max-width: 640px) {
  .nav-container {
    padding: 0 0.9rem;
  }

  .brand-mark {
    width: 2.38rem;
    height: 2.38rem;
  }

  .brand-title {
    max-width: 10ch;
    overflow: hidden;
    text-overflow: ellipsis;
  }
}
</style>
