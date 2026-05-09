<template>
  <button
    :class="variant === 'mobile' ? 'mobile-profile' : 'user-info'"
    type="button"
    @click="$emit('profile')"
  >
    <span class="avatar">
      <img
        v-if="avatarDisplayUrl && !hasAvatarError"
        :src="avatarDisplayUrl"
        alt=""
        class="avatar-image"
        @error="$emit('avatar-error')"
      />
      <span v-else class="default-avatar">{{ usernameInitial }}</span>
    </span>
    <span :class="variant === 'mobile' ? 'mobile-profile-copy' : 'user-copy'">
      <strong>{{ username }}</strong>
      <span>个人资料</span>
    </span>
    <AppIcon
      v-if="variant === 'mobile'"
      icon="lucide:chevron-right"
      class="mobile-chevron"
    />
  </button>
</template>

<script setup lang="ts">
import AppIcon from "@/shared/ui/branding/AppIcon.vue";

withDefaults(
  defineProps<{
    avatarDisplayUrl?: string;
    hasAvatarError: boolean;
    username: string;
    usernameInitial: string;
    variant?: "desktop" | "mobile";
  }>(),
  {
    avatarDisplayUrl: "",
    variant: "desktop",
  },
);

defineEmits<{
  (event: "profile"): void;
  (event: "avatar-error"): void;
}>();
</script>

<style scoped lang="scss">
.user-info {
  display: inline-flex;
  align-items: center;
  gap: 0.58rem;
  min-width: 0;
  max-width: 15rem;
  padding: 0.3rem 0.42rem;
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: 999px;
  background: linear-gradient(
    180deg,
    rgba(255, 255, 255, 0.88),
    rgba(255, 255, 255, 0.76)
  );
  box-shadow: 0 16px 30px -26px rgba(15, 23, 42, 0.16);
  cursor: pointer;
  transition:
    transform var(--duration-fast) var(--ease-standard),
    border-color var(--duration-fast) var(--ease-standard),
    background var(--duration-fast) var(--ease-standard);
}

.user-info:hover {
  border-color: rgba(99, 102, 241, 0.26);
  background: rgba(255, 255, 255, 0.94);
  transform: translateY(-1px);
}

.mobile-profile {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  width: 100%;
  padding: 0.95rem 1rem;
  border: 1px solid rgba(99, 102, 241, 0.16);
  border-radius: 1.3rem;
  background: linear-gradient(
    135deg,
    rgba(219, 234, 254, 0.84),
    rgba(255, 255, 255, 0.96)
  );
  color: var(--color-text-dark);
  cursor: pointer;
  text-align: left;
}

.avatar {
  display: inline-flex;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  width: 2.18rem;
  height: 2.18rem;
  border-radius: 999px;
  background: var(--grad-primary);
  box-shadow: 0 16px 24px -18px rgba(79, 70, 229, 0.58);
  color: #ffffff;
  font-weight: 700;
}

.default-avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  font-size: 0.9rem;
  text-transform: uppercase;
}

.avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.user-copy,
.mobile-profile-copy {
  display: flex;
  min-width: 0;
  flex-direction: column;
  text-align: left;
}

.mobile-profile-copy {
  flex: 1;
  gap: 0.2rem;
}

.user-copy strong,
.user-copy span,
.mobile-profile-copy strong,
.mobile-profile-copy span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-copy strong {
  color: var(--color-text-dark);
  font-size: 0.88rem;
}

.user-copy span {
  color: var(--color-text-subtle);
  font-size: 0.76rem;
}

.mobile-profile-copy span {
  color: var(--color-text-muted);
  font-size: 0.88rem;
}

.mobile-chevron {
  flex-shrink: 0;
  width: 1rem;
  height: 1rem;
  color: #94a3b8;
}

@media (max-width: 1180px) {
  .user-info {
    max-width: 13.2rem;
  }
}

@media (max-width: 1024px) {
  .user-info {
    display: none;
  }
}
</style>
