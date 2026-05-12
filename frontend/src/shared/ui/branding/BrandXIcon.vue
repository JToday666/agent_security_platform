<template>
  <svg
    v-bind="$attrs"
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="currentColor"
    xmlns="http://www.w3.org/2000/svg"
  >
    <title v-if="title">{{ title }}</title>
    <path
      d="M18.901 1.153h3.68l-8.04 9.19L24 22.846h-7.406l-5.8-7.584-6.638 7.584H.474l8.6-9.83L0 1.154h7.594l5.243 6.932 6.064-6.933Zm-1.291 19.491h2.039L6.486 3.24H4.298L17.61 20.644Z"
    />
  </svg>
</template>

<script setup lang="ts">
defineProps<{
  size?: string | number;
  title?: string;
}>();
</script>
