<template>
  <div class="content not-found-page layout-page-shell">
    <PageHero
      eyebrow="404"
      title="页面未找到"
      description="当前地址暂不可访问，请从导航或下方入口重新进入。"
      align="center"
    />

    <SectionBlock
      class="not-found-section"
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
    </SectionBlock>
  </div>
</template>

<script setup lang="ts">
import { RouteLocation } from "@/app/router/route-names";
import PageHero from "@/shared/ui/page/PageHero.vue";
import SectionBlock from "@/shared/ui/page/SectionBlock.vue";
import UiButton from "@/shared/ui/actions/UiButton.vue";
</script>

<style scoped lang="scss">
.not-found-section {
  gap: 0.9rem;
}

.not-found-section :deep(.section-block__head),
.not-found-section :deep(.section-block__copy) {
  align-items: center;
  text-align: center;
}

.not-found-section :deep(.section-block__actions) {
  justify-content: center;
}
</style>
