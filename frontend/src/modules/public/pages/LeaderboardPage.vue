<template>
  <div class="content leaderboard-page layout-page-shell layout-page-shell--wide">
    <PageHeroCard
      title="排行榜"
      description="当前版本仅展示已接入的真实能力，不提供模拟榜单。"
      tone="showcase"
      title-tone="brand"
    />

    <section class="placeholder-card ui-surface-panel">
      <h2>公开结果暂未开放</h2>

      <div class="placeholder-actions">
        <UiButton :to="RouteLocation.datasetList" variant="primary">
          浏览数据集
        </UiButton>
        <UiButton :to="RouteLocation.contact" variant="secondary">
          联系我们
        </UiButton>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import PageHeroCard from "@/shared/ui/page/PageHeroCard.vue";
import UiButton from "@/shared/ui/actions/UiButton.vue";
import { RouteLocation } from "@/app/router/route-names";
</script>

<style scoped lang="scss">
.leaderboard-page {
  padding-bottom: 2.5rem;
}

.placeholder-card {
  border-radius: 1.5rem;
  padding: 1.5rem;
}

.placeholder-card h2 {
  margin: 0;
  color: var(--color-text-dark);
}

.placeholder-card p {
  margin: 0.75rem 0 0;
  color: var(--color-text-subtle);
  line-height: 1.75;
}

.placeholder-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-top: 1rem;
}

@media (max-width: 768px) {
  .placeholder-actions {
    flex-direction: column;
  }
}
</style>
