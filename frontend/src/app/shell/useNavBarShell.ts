import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { storeToRefs } from "pinia";
import { useRoute, useRouter } from "vue-router";
import { RouteLocation } from "@/app/router/route-names";
import { EXPLORE_NAV_ITEMS, WORKSPACE_NAV_ITEMS } from "@/app/shell/nav-items";
import { resolveShellContext } from "@/app/shell/shell-context";
import { useUserStore } from "@/modules/account/stores/userStore";

const MOBILE_NAV_BREAKPOINT = 1120;
const SCROLL_THRESHOLD = 10;
const MOUSE_TOP_THRESHOLD = 10;

export const useNavBarShell = () => {
  const route = useRoute();
  const router = useRouter();
  const userStore = useUserStore();
  const { avatarDisplayUrl, isLogin, username } = storeToRefs(userStore);

  const isVisible = ref(true);
  const mobileMenuOpen = ref(false);
  const hasAvatarError = ref(false);

  let lastScrollY = 0;
  let ticking = false;

  const shellContext = computed(() =>
    resolveShellContext(route.name ? String(route.name) : undefined),
  );

  const mainNavItems = computed(() =>
    shellContext.value === "workspace"
      ? WORKSPACE_NAV_ITEMS.filter(
          (item) => !item.requiresAuth || isLogin.value,
        )
      : EXPLORE_NAV_ITEMS,
  );

  const secondaryNavItems = computed(() => {
    if (shellContext.value === "workspace") {
      return EXPLORE_NAV_ITEMS;
    }

    if (!isLogin.value) {
      return [];
    }

    return WORKSPACE_NAV_ITEMS.filter(
      (item) => !item.requiresAuth || isLogin.value,
    );
  });

  const usernameInitial = computed(
    () => (username.value || "A").trim().charAt(0).toUpperCase() || "A",
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
    goToProfile();
  };

  const openLoginDialog = () => {
    userStore.openLoginDialog();
  };

  const openLoginDialogFromMenu = () => {
    closeMobileMenu();
    openLoginDialog();
  };

  const markAvatarError = () => {
    hasAvatarError.value = true;
  };

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

  watch(avatarDisplayUrl, () => {
    hasAvatarError.value = false;
  });

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

  return {
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
    secondaryNavItems,
    shellContext,
    toggleMobileMenu,
    username,
    usernameInitial,
  };
};
