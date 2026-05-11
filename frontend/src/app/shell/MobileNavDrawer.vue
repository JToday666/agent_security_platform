<template>
  <aside
    id="mobile-nav-drawer"
    class="mobile-nav-drawer"
    :class="{ 'mobile-nav-drawer--open': open }"
  >
    <div class="mobile-drawer-head">
      <strong class="mobile-drawer-title">{{ t("layout.mobile.title") }}</strong>
      <button
        class="mobile-close"
        type="button"
        :aria-label="t('layout.aria.closeMenu')"
        @click="$emit('close')"
      >
        <AppIcon icon="lucide:x" class="mobile-close-icon" />
      </button>
    </div>

    <UserNavMenu
      v-if="isLogin"
      variant="mobile"
      :avatar-display-url="avatarDisplayUrl"
      :has-avatar-error="hasAvatarError"
      :username="username"
      :username-initial="usernameInitial"
      @profile="$emit('profile')"
      @avatar-error="$emit('avatar-error')"
    />

    <UiButton
      v-else
      class="mobile-cta"
      as="button"
      variant="primary"
      leading-icon="lucide:log-in"
      @click="$emit('open-login')"
    >
      <span>{{ t("common.actions.loginRegister") }}</span>
    </UiButton>

    <div class="mobile-nav-group">
      <p class="mobile-group-label">{{ t("layout.mobile.primaryGroup") }}</p>
      <router-link
        v-for="item in mainNavItems"
        :key="`mobile-main-${item.key}`"
        v-bind="getNavLinkStateProps(item)"
        :to="item.to"
        class="mobile-nav-link"
        @click="$emit('close')"
      >
        <span class="mobile-link-main">
          <AppIcon :icon="item.icon" class="nav-link-icon" />
          <span>{{ item.label }}</span>
        </span>
        <AppIcon icon="lucide:chevron-right" class="mobile-chevron" />
      </router-link>
    </div>

    <div v-if="secondaryNavItems.length" class="mobile-nav-group">
      <p class="mobile-group-label">{{ t("layout.mobile.secondaryGroup") }}</p>
      <router-link
        v-for="item in secondaryNavItems"
        :key="`mobile-secondary-${item.key}`"
        v-bind="getNavLinkStateProps(item)"
        :to="item.to"
        class="mobile-nav-link mobile-nav-link--secondary"
        @click="$emit('close')"
      >
        <span class="mobile-link-main">
          <AppIcon :icon="item.icon" class="nav-link-icon" />
          <span>{{ item.label }}</span>
        </span>
        <AppIcon icon="lucide:chevron-right" class="mobile-chevron" />
      </router-link>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { useI18n } from "vue-i18n";
import { getNavLinkStateProps } from "@/app/shell/nav-link-state";
import type { AppNavItem } from "@/app/shell/nav-items";
import UserNavMenu from "@/app/shell/UserNavMenu.vue";
import UiButton from "@/shared/ui/actions/UiButton.vue";
import AppIcon from "@/shared/ui/branding/AppIcon.vue";

const { t } = useI18n();

defineProps<{
  avatarDisplayUrl: string;
  hasAvatarError: boolean;
  isLogin: boolean;
  mainNavItems: AppNavItem[];
  open: boolean;
  secondaryNavItems: AppNavItem[];
  username: string;
  usernameInitial: string;
}>();

defineEmits<{
  (event: "avatar-error"): void;
  (event: "close"): void;
  (event: "open-login"): void;
  (event: "profile"): void;
}>();
</script>

<style scoped lang="scss">
.mobile-nav-drawer {
  position: fixed;
  top: var(--nav-height);
  right: 0;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  overflow-y: auto;
  width: min(90vw, 390px);
  height: calc(100vh - var(--nav-height));
  padding: 1rem;
  border-left: 1px solid rgba(148, 163, 184, 0.18);
  background: linear-gradient(
    180deg,
    rgba(255, 255, 255, 0.98),
    rgba(244, 247, 255, 0.98)
  );
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
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.35rem;
  height: 2.35rem;
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 999px;
  background: #ffffff;
  color: var(--color-text-dark);
  cursor: pointer;
}

.mobile-close-icon,
.nav-link-icon,
.mobile-chevron {
  width: 1rem;
  height: 1rem;
}

.mobile-close-icon {
  width: 1.15rem;
  height: 1.15rem;
}

.mobile-cta {
  width: 100%;
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
  letter-spacing: 0;
  text-transform: uppercase;
}

.mobile-nav-link {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.95rem 1rem;
  border: 1px solid transparent;
  border-radius: 1.1rem;
  background: rgba(255, 255, 255, 0.92);
  color: #334155;
  text-decoration: none;
  transition:
    transform var(--duration-fast) var(--ease-standard),
    border-color var(--duration-fast) var(--ease-standard),
    background var(--duration-fast) var(--ease-standard);
}

.mobile-nav-link.active {
  border-color: rgba(99, 102, 241, 0.18);
  background: linear-gradient(
    135deg,
    rgba(219, 234, 254, 0.8),
    rgba(255, 255, 255, 0.98)
  );
  color: var(--color-primary);
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
  flex-shrink: 0;
  color: #94a3b8;
}

@media (max-width: 640px) {
  .mobile-nav-drawer {
    width: 100%;
    max-width: none;
  }
}
</style>
