<template>
  <nav class="navbar" :class="{ hidden: !isVisible }">
    <div class="nav-container">
      <router-link :to="RouteLocation.home" class="logo">智能体安全评测</router-link>

      <div class="right-section">
        <div class="nav-links">
          <router-link :to="RouteLocation.home" class="nav-link" exact-active-class="active"
            ><AppIcon icon="lucide:house" class="nav-link-icon" />
            <span>首页</span></router-link
          >
          <router-link :to="RouteLocation.datasetList" class="nav-link" active-class="active"
            ><AppIcon icon="lucide:database" class="nav-link-icon" />
            <span>评测目录</span></router-link
          >
          <router-link :to="RouteLocation.leaderboard" class="nav-link" active-class="active"
            ><AppIcon icon="lucide:trophy" class="nav-link-icon" />
            <span>排行榜</span></router-link
          >
          <router-link :to="RouteLocation.contact" class="nav-link" active-class="active"
            ><AppIcon icon="lucide:mail" class="nav-link-icon" />
            <span>联系我们</span></router-link
          >
          <router-link
            v-if="isLogin"
            :to="RouteLocation.userCenter"
            class="nav-link"
            active-class="active"
            ><AppIcon icon="lucide:layout-dashboard" class="nav-link-icon" />
            <span>个人中心</span></router-link
          >
        </div>

        <div
          v-if="isLogin"
          class="user-info"
          @click="goToProfile"
          :title="'修改个人信息'"
        >
          <div class="avatar">
            <span class="default-avatar">{{
              username.charAt(0).toUpperCase()
            }}</span>
          </div>
          <span class="username">{{ username }}</span>
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from "vue";
import { useRouter } from "vue-router";
import { useUserStore } from "@/store/UserStore";
import { storeToRefs } from "pinia";
import AppIcon from "@/components/icon/AppIcon.vue";
import { RouteLocation } from "@/router/RouteNames";

const router = useRouter();
const userStore = useUserStore();
const { isLogin, username } = storeToRefs(userStore);

const isVisible = ref(true);
let lastScrollY = window.scrollY;
const SCROLL_THRESHOLD = 10;
const MOUSE_TOP_THRESHOLD = 10;

const handleScroll = () => {
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

const handleMouseMove = (e: MouseEvent) => {
  if (e.clientY <= MOUSE_TOP_THRESHOLD) {
    isVisible.value = true;
  }
};

let ticking = false;
const onScroll = () => {
  if (!ticking) {
    requestAnimationFrame(() => {
      handleScroll();
      ticking = false;
    });
    ticking = true;
  }
};

onMounted(() => {
  window.addEventListener("scroll", onScroll);
  window.addEventListener("mousemove", handleMouseMove);
  lastScrollY = window.scrollY;
});

onUnmounted(() => {
  window.removeEventListener("scroll", onScroll);
  window.removeEventListener("mousemove", handleMouseMove);
});

const goToProfile = () => {
  router.push(RouteLocation.userProfile);
};
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
  transition: transform 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  transform: translateY(0);
}

.navbar.hidden {
  transform: translateY(-100%);
}

.nav-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 2rem;
  height: var(--nav-height);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.logo {
  font-size: 1.6rem;
  font-weight: 800;
  background: linear-gradient(135deg, #2563eb, #7c3aed);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  text-decoration: none;
  letter-spacing: -0.5px;
  transition: opacity 0.2s;
}

.logo:hover {
  opacity: 0.8;
}

.right-section {
  display: flex;
  align-items: center;
  gap: 2rem;
}

.nav-links {
  display: flex;
  gap: 1.8rem;
  align-items: center;
}

.nav-link {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  color: #334155;
  text-decoration: none;
  font-weight: 500;
  font-size: 1rem;
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

.nav-link:hover {
  color: #2563eb;
}

.nav-link:hover::after {
  width: 100%;
}

.nav-link.active {
  color: #2563eb;
  font-weight: 600;
}

.nav-link.active::after {
  width: 100%;
  background: linear-gradient(90deg, #2563eb, #7c3aed);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  cursor: pointer;
  padding: 0.3rem 0.8rem 0.3rem 0.4rem;
  border-radius: 40px;
  background: rgba(255, 255, 255, 0.3);
  transition:
    background 0.2s,
    box-shadow 0.2s;
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
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  font-size: 1rem;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.3);
}

.default-avatar {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: inherit;
  color: white;
  font-weight: 600;
  font-size: 1.2rem;
  text-transform: uppercase;
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

@media (max-width: 768px) {
  .nav-container {
    padding: 0 1rem;
  }

  .nav-links {
    gap: 1.2rem;
  }

  .right-section {
    gap: 1rem;
  }

  .username {
    max-width: 80px;
  }
}

@media (max-width: 640px) {
  .logo {
    font-size: 1.4rem;
  }

  .nav-link {
    font-size: 0.9rem;
  }

  .username {
    display: none;
  }

  .user-info {
    padding: 0.2rem 0.4rem 0.2rem 0.2rem;
  }
}
</style>
