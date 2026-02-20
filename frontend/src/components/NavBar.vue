<template>
  <nav class="navbar" :class="{ hidden: !isVisible }">
    <div class="nav-container">
      <!-- 左侧 Logo -->
      <router-link to="/" class="logo">安全评测</router-link>

      <!-- 右侧区域：导航链接 + 用户信息（登录后显示） -->
      <div class="right-section">
        <!-- 导航链接区域 -->
        <div class="nav-links">
          <router-link to="/" class="nav-link" active-class="active">首页</router-link>
          <router-link to="/dataset" class="nav-link" active-class="active">数据集</router-link>
          <router-link to="/leaderboard" class="nav-link" active-class="active">排行榜</router-link>
          <router-link to="/contact" class="nav-link" active-class="active">联系我们</router-link>
          <router-link v-if="isLogin" to="/user" class="nav-link" active-class="active"
            >个人中心</router-link
          >
        </div>

        <!-- 登录后显示头像和用户名 -->
        <div v-if="isLogin" class="user-info" @click="goToProfile" :title="'修改个人信息'">
          <div class="avatar">
            <span class="default-avatar">{{ username.charAt(0).toUpperCase() }}</span>
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
import { useUserStore } from "@/store/user";
import { storeToRefs } from "pinia";

const router = useRouter();
const userStore = useUserStore();
const { isLogin, username } = storeToRefs(userStore);

// 导航栏显示状态（滚动隐藏/显示）
const isVisible = ref(true);
let lastScrollY = window.scrollY;
const SCROLL_THRESHOLD = 10;
const MOUSE_TOP_THRESHOLD = 10;

const handleScroll = () => {
  const currentScrollY = window.scrollY;
  const scrollingDown = currentScrollY > lastScrollY && currentScrollY > SCROLL_THRESHOLD;
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

// 跳转到修改信息页面
const goToProfile = () => {
  router.push("/profile");
};
</script>

<style scoped>
.navbar {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  box-shadow: 0 2px 20px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  transition: transform 0.3s ease;
  transform: translateY(0);
}

.navbar.hidden {
  transform: translateY(-100%);
}

.nav-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 2rem;
  height: 70px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.logo {
  font-size: 1.5rem;
  font-weight: 700;
  color: #3b82f6;
  text-decoration: none;
  letter-spacing: -0.5px;
  transition: color 0.2s;
}

.logo:hover {
  color: #2563eb;
}

.right-section {
  display: flex;
  align-items: center;
  gap: 1.5rem; /* 保持导航链接与用户信息之间的间距 */
}

.nav-links {
  display: flex;
  gap: 1.5rem;
  align-items: center;
  margin-left: auto;
}

.nav-link {
  color: #1e293b;
  text-decoration: none;
  font-weight: 500;
  font-size: 1rem;
  padding: 0.5rem 0;
  position: relative;
  transition: color 0.2s;
}

.nav-link::after {
  content: "";
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 0;
  height: 2px;
  background: #3b82f6;
  transition: width 0.2s ease;
}

.nav-link:hover {
  color: #3b82f6;
}

.nav-link:hover::after {
  width: 100%;
}

.nav-link.active {
  color: #3b82f6;
  font-weight: 600;
}

.nav-link.active::after {
  width: 100%;
  background: #3b82f6;
}

/* 用户信息区域 */
.user-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  padding: 0.4rem 0.8rem;
  border-radius: 40px;
  transition: background 0.2s;
}

.user-info:hover {
  background: rgba(0, 0, 0, 0.05);
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  overflow: hidden;
  background: #3b82f6;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  font-size: 1rem;
}

.default-avatar {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #3b82f6;
  color: white;
  font-weight: 600;
  font-size: 1.2rem;
  text-transform: uppercase;
}

.username {
  font-size: 1rem;
  font-weight: 500;
  color: #1e293b;
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .nav-container {
    padding: 0 1rem;
  }
  .nav-links {
    gap: 1rem;
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
    font-size: 1.2rem;
  }
  .nav-link {
    font-size: 0.9rem;
  }
  .username {
    display: none; /* 小屏隐藏用户名，只保留头像 */
  }
  .user-info {
    padding: 0.2rem 0.4rem;
  }
}
</style>
