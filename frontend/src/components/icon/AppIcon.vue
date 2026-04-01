<template>
  <Icon
    v-bind="attrs"
    :icon="icon"
    :width="size"
    :height="size"
    :title="title"
    :aria-hidden="decorative ? 'true' : undefined"
    :role="decorative ? undefined : 'img'"
  />
</template>

<script setup lang="ts">
import { Icon } from "@iconify/vue";
import { useAttrs } from "vue";

defineOptions({
  inheritAttrs: false,
});

// 统一包装第三方图标组件，便于全站控制尺寸和可访问性属性。
withDefaults(
  defineProps<{
    icon: string;
    size?: string | number;
    decorative?: boolean;
    title?: string;
  }>(),
  {
    size: "1em",
    decorative: true,
    title: undefined,
  },
);

const attrs = useAttrs();
</script>
