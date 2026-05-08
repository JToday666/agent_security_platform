<template>
  <SectionBlock title="状态摘要">
    <div class="summary-surface">
      <dl class="summary-grid">
        <div
          v-for="item in items"
          :key="item.label"
          class="summary-item"
        >
          <dt>{{ item.label }}</dt>
          <dd v-if="item.kind === 'status'">
            <AgentStatusTag :status="detail.status" />
          </dd>
          <dd v-else>{{ item.value }}</dd>
        </div>
      </dl>
      <p class="detail-description">{{ detail.description || "暂无描述" }}</p>
    </div>
  </SectionBlock>
</template>

<script setup lang="ts">
import AgentStatusTag from "@/modules/agent/components/AgentStatusTag.vue";
import type { AgentDetailTextItem } from "@/modules/agent/lib/agent-detail-view";
import type { AgentDetail } from "@/shared/types/agent-registry-types";
import SectionBlock from "@/shared/ui/page/SectionBlock.vue";

defineProps<{
  detail: AgentDetail;
  items: AgentDetailTextItem[];
}>();
</script>

<style scoped lang="scss">
.summary-surface {
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
  padding: 1rem;
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: var(--radius-control-sm);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(248, 250, 252, 0.86)),
    rgba(255, 255, 255, 0.76);
  box-shadow: 0 16px 36px rgba(15, 23, 42, 0.06);
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.35rem 1.15rem;
  margin: 0;
}

.summary-item {
  min-width: 0;
  padding-block: 0.1rem;
}

.summary-item dt {
  color: var(--color-text-subtle);
  font-size: 0.86rem;
}

.summary-item dd {
  margin: 0.32rem 0 0;
  color: var(--color-text-dark);
  font-weight: 700;
  overflow-wrap: anywhere;
  line-height: 1.55;
}

.detail-description {
  margin: 0;
  padding-top: 0.9rem;
  border-top: 1px solid var(--color-border-soft);
  color: var(--color-text-muted);
  line-height: 1.65;
}

@media (max-width: 860px) {
  .summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 700px) {
  .summary-grid {
    grid-template-columns: 1fr;
  }
}
</style>
