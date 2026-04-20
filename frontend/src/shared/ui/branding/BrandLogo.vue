<template>
  <img
    :src="brandLogoUrl"
    :alt="alt"
    class="brand-logo"
    :loading="priority ? 'eager' : 'lazy'"
    :fetchpriority="priority ? 'high' : 'auto'"
    decoding="async"
    draggable="false"
  />
</template>

<script setup lang="ts">
import brandLogoUrl from "@/shared/assets/branding/logo.svg";

withDefaults(
  defineProps<{
    alt?: string;
    priority?: boolean;
  }>(),
  {
    alt: "智能体安全评测平台标志",
    priority: false,
  },
);
</script>

<style scoped lang="scss">
.brand-logo {
  display: block;
  width: 100%;
  height: auto;
  object-fit: contain;
}
</style>
