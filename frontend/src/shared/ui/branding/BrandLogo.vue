<template>
  <img
    :src="brandLogoUrl"
    :alt="resolvedAlt"
    class="brand-logo"
    :loading="priority ? 'eager' : 'lazy'"
    :fetchpriority="priority ? 'high' : 'auto'"
    decoding="async"
    draggable="false"
  />
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import brandLogoUrl from "@/shared/assets/branding/logo.svg";

const props = withDefaults(
  defineProps<{
    alt?: string;
    priority?: boolean;
  }>(),
  {
    alt: "",
    priority: false,
  },
);

const { t } = useI18n();
const resolvedAlt = computed(() => props.alt || t("common.brand.logoAlt"));
</script>

<style scoped lang="scss">
.brand-logo {
  display: block;
  width: 100%;
  height: auto;
  object-fit: contain;
}
</style>
