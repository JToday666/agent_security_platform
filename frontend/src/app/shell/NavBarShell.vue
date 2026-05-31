<template>
  <nav
    class="navbar"
    :class="[
      `navbar--${shellContext}`,
      { 'navbar--hidden': !isVisible && !mobileMenuOpen },
    ]"
  >
    <DesktopNavBar
      :avatar-display-url="avatarDisplayUrl"
      :has-avatar-error="hasAvatarError"
      :is-login="isLogin"
      :main-nav-items="mainNavItems"
      :mobile-menu-open="mobileMenuOpen"
      :overflow-nav-items="overflowNavItems"
      :overflow-nav-label="overflowNavLabel"
      :shell-context="shellContext"
      :username="username"
      :username-initial="usernameInitial"
      @avatar-error="markAvatarError"
      @open-login="openLoginDialog"
      @profile="goToProfile"
      @toggle-mobile-menu="toggleMobileMenu"
    />

    <div
      v-if="mobileMenuOpen"
      class="mobile-nav-overlay"
      aria-hidden="true"
      @click="closeMobileMenu"
    ></div>

    <MobileNavDrawer
      :avatar-display-url="avatarDisplayUrl"
      :has-avatar-error="hasAvatarError"
      :is-login="isLogin"
      :main-nav-items="mainNavItems"
      :open="mobileMenuOpen"
      :secondary-nav-items="secondaryNavItems"
      :username="username"
      :username-initial="usernameInitial"
      @avatar-error="markAvatarError"
      @close="closeMobileMenu"
      @open-login="openLoginDialogFromMenu"
      @profile="goToProfileFromMenu"
    />
  </nav>
</template>

<script setup lang="ts">
import DesktopNavBar from "@/app/shell/DesktopNavBar.vue";
import MobileNavDrawer from "@/app/shell/MobileNavDrawer.vue";
import { useNavBarShell } from "@/app/shell/useNavBarShell";

const {
  avatarDisplayUrl,
  closeMobileMenu,
  goToProfile,
  goToProfileFromMenu,
  hasAvatarError,
  isLogin,
  isVisible,
  mainNavItems,
  markAvatarError,
  mobileMenuOpen,
  openLoginDialog,
  openLoginDialogFromMenu,
  overflowNavItems,
  overflowNavLabel,
  secondaryNavItems,
  shellContext,
  toggleMobileMenu,
  username,
  usernameInitial,
} = useNavBarShell();
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

.navbar--hidden {
  transform: translateY(-100%);
}

.navbar--public {
  background: linear-gradient(
    180deg,
    rgba(255, 255, 255, 0.9),
    rgba(255, 255, 255, 0.78)
  );
  box-shadow:
    0 18px 36px -30px rgba(79, 70, 229, 0.24),
    inset 0 -1px 0 rgba(255, 255, 255, 0.58);
}

.navbar--workspace {
  background: linear-gradient(
    180deg,
    rgba(255, 255, 255, 0.9),
    rgba(255, 255, 255, 0.8)
  );
  box-shadow:
    0 16px 30px -28px rgba(15, 23, 42, 0.16),
    inset 0 -1px 0 rgba(255, 255, 255, 0.58);
}

.mobile-nav-overlay {
  position: fixed;
  inset: var(--nav-height) 0 0;
  background: rgba(15, 23, 42, 0.24);
  backdrop-filter: blur(4px);
}
</style>
