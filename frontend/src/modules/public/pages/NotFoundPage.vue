<template>
  <div class="content not-found-page layout-page-shell">
    <PageHeroCard
      eyebrow="404"
      title="页面未找到"
      description="当前地址不在系统支持范围内，请从导航或下方入口重新进入。"
    />

    <SectionCard
      class="not-found-card layout-page-panel layout-page-panel--md"
      title="可用入口"
      description="您可以返回首页，或从评测目录重新开始浏览。"
    >
      <template #actions>
        <UiButton :to="RouteLocation.home" variant="secondary">
          返回首页
        </UiButton>
        <UiButton :to="RouteLocation.datasetList" variant="primary">
          查看评测目录
        </UiButton>
      </template>
    </SectionCard>
  </div>
</template>

<script setup lang="ts">
import { RouteLocation } from "@/app/router/RouteNames";
import PageHeroCard from "@/shared/ui/page/PageHeroCard.vue";
import SectionCard from "@/shared/ui/page/SectionCard.vue";
import UiButton from "@/shared/ui/actions/UiButton.vue";
</script>

<style scoped>
.not-found-card {
  gap: 0.9rem;
}
</style>