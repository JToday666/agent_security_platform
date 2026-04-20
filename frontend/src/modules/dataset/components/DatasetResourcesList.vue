<template>
  <section class="resources-card layout-section-card ui-surface-white">
    <div class="layout-section-head">
      <h2>资源与示例</h2>
      <p>仅展示当前接口已返回的文档、下载、演示或外链资源。</p>
    </div>

    <div v-if="resources.length" class="resource-list">
      <article
        v-for="resource in resources"
        :key="resource.label + resource.url"
        class="resource-item"
      >
        <div class="resource-copy">
          <strong>{{ resource.label }}</strong>
          <span>{{ typeLabels[resource.type] }}</span>
        </div>
        <Button :href="resource.url" target="_blank" variant="secondary" size="sm">
          查看资源
        </Button>
      </article>
    </div>

    <InlineNotice
      v-else
      tone="info"
      title="暂无资源"
      message="当前数据集没有返回可展示的外部资源。"
    />
  </section>
</template>

<script setup lang="ts">
import type { DatasetResourceLink } from "@/shared/types/dataset-types";
import Button from "@/shared/ui/actions/UiButton.vue";
import InlineNotice from "@/shared/ui/feedback/InlineNotice.vue";

defineProps<{
  resources: DatasetResourceLink[];
}>();

const typeLabels: Record<DatasetResourceLink["type"], string> = {
  docs: "文档",
  download: "下载",
  demo: "演示",
  link: "链接",
};
</script>

<style scoped lang="scss">
.resource-list {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.resource-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.9rem 1rem;
  border: 1px solid rgba(148, 163, 184, 0.14);
  border-radius: 1rem;
  background: rgba(248, 250, 252, 0.78);
}

.resource-copy {
  display: flex;
  flex-direction: column;
  gap: 0.28rem;
  min-width: 0;
}

.resource-copy strong {
  color: var(--color-text-dark);
}

.resource-copy span {
  color: var(--color-text-subtle);
  font-size: 0.88rem;
}

@media (max-width: 640px) {
  .resource-item {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
