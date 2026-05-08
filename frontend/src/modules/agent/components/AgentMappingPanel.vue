<template>
  <div class="detail-section-pair">
    <SectionBlock title="输入字段逻辑映射">
      <div class="mapping-tree">
        <article
          v-for="item in inputItems"
          :key="item.label"
          class="mapping-node ui-glow-frame"
        >
          <div class="mapping-node__source">
            <span class="mapping-n-label">{{ item.sourceLabel }}</span>
            <strong class="mapping-n-value">{{ item.source }}</strong>
          </div>
          <div class="mapping-node__connector">
            <span class="mapping-line"></span>
            <span class="mapping-arrow-ring">
              <AppIcon icon="lucide:arrow-right" class="mapping-arrow" />
            </span>
            <span class="mapping-line"></span>
          </div>
          <div class="mapping-node__target">
            <span class="mapping-n-label">{{ item.targetLabel }}</span>
            <code class="mapping-n-code" :class="{ 'is-empty': item.empty }">{{ item.target }}</code>
          </div>
        </article>
      </div>
    </SectionBlock>

    <SectionBlock title="输出字段逻辑映射">
      <div class="mapping-tree mapping-tree--reverse">
        <article
          v-for="item in outputItems"
          :key="item.label"
          class="mapping-node ui-glow-frame"
        >
          <div class="mapping-node__source">
            <span class="mapping-n-label">{{ item.sourceLabel }}</span>
            <code class="mapping-n-code" :class="{ 'is-empty': item.empty }">{{ item.source }}</code>
          </div>
          <div class="mapping-node__connector">
            <span class="mapping-line"></span>
            <span class="mapping-arrow-ring">
              <AppIcon icon="lucide:arrow-right" class="mapping-arrow" />
            </span>
            <span class="mapping-line"></span>
          </div>
          <div class="mapping-node__target">
            <span class="mapping-n-label">{{ item.targetLabel }}</span>
            <strong class="mapping-n-value">{{ item.target }}</strong>
          </div>
        </article>
      </div>
    </SectionBlock>
  </div>
</template>

<script setup lang="ts">
import AppIcon from "@/shared/ui/branding/AppIcon.vue";
import type { AgentMappingDisplayItem } from "@/modules/agent/lib/agent-detail-view";
import SectionBlock from "@/shared/ui/page/SectionBlock.vue";

defineProps<{
  inputItems: AgentMappingDisplayItem[];
  outputItems: AgentMappingDisplayItem[];
}>();
</script>

<style scoped lang="scss">
.detail-section-pair {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1.15rem;
  align-items: start;
}

.mapping-tree {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.mapping-node {
  display: flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid var(--color-border-soft);
  border-radius: var(--radius-card-sm);
  padding: 1rem;
  box-shadow: 0 4px 12px -8px rgba(15, 23, 42, 0.08);
  transition:
    border-color var(--duration-fast) var(--ease-standard),
    box-shadow var(--duration-fast) var(--ease-standard),
    transform var(--duration-fast) var(--ease-standard);
}

.mapping-node:hover,
.mapping-node:focus-within {
  border-color: rgba(99, 102, 241, 0.24);
  box-shadow: var(--shadow-surface-soft);
  transform: translateY(-1px);
}

.mapping-tree--reverse .mapping-node {
  background:
    linear-gradient(90deg, rgba(240, 253, 250, 0.54), rgba(255, 255, 255, 0.86)),
    rgba(255, 255, 255, 0.9);
}

.mapping-node__source,
.mapping-node__target {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.mapping-node__target {
  align-items: flex-end;
  text-align: right;
}

.mapping-n-label {
  font-size: 0.78rem;
  color: var(--color-text-subtle);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 600;
}

.mapping-n-value {
  font-size: 1rem;
  font-weight: 500;
  color: var(--color-text-main);
  word-break: break-all;
}

.mapping-n-code {
  font-size: 0.95rem;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas,
    "Liberation Mono", "Courier New", monospace;
  background: var(--color-surface-muted);
  color: #0369a1;
  padding: 0.25rem 0.5rem;
  border-radius: 0.4rem;
  border: 1px solid rgba(148, 163, 184, 0.16);
  word-break: break-all;

  &.is-empty {
    opacity: 0.4;
    text-decoration: line-through;
  }
}

.mapping-node__connector {
  display: flex;
  align-items: center;
  padding: 0 1rem;
  color: var(--color-primary);
  opacity: 0.8;
}

.mapping-line {
  flex: 1;
  height: 2px;
  min-width: 2rem;
  background: var(--grad-progress);
  opacity: 0.4;
}

.mapping-arrow-ring {
  background: var(--color-primary-soft);
  color: var(--color-primary);
  border-radius: 50%;
  padding: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 10px rgba(37, 99, 235, 0.2);
  z-index: 1;
}

@media (max-width: 1080px) {
  .detail-section-pair {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 700px) {
  .mapping-node {
    flex-direction: column;
    align-items: stretch;
  }

  .mapping-node__target {
    align-items: flex-start;
    text-align: left;
  }

  .mapping-node__connector {
    align-self: center;
    padding: 0.65rem 0;
    transform: rotate(90deg);
  }
}
</style>
