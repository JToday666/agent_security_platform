<template>
  <div class="agent-connection-panel">
    <SectionBlock :title="t('agent.detail.sections.connection')">
      <dl class="detail-grid">
        <div
          v-for="item in connectionItems"
          :key="item.label"
          class="detail-field"
        >
          <dt>{{ item.label }}</dt>
          <dd>{{ item.value }}</dd>
        </div>
      </dl>
    </SectionBlock>

    <SectionBlock :title="t('agent.detail.sections.authSummary')">
      <dl class="detail-grid">
        <div
          v-for="item in authItems"
          :key="item.label"
          class="detail-field"
        >
          <dt>{{ item.label }}</dt>
          <dd>{{ item.value }}</dd>
        </div>
      </dl>
    </SectionBlock>

    <SectionBlock :title="t('agent.detail.sections.customFields')">
      <AgentCodePreview
        :code="customRequestBodyJson"
        language="json"
        max-height="360px"
      />
    </SectionBlock>

    <SectionBlock :title="t('agent.detail.sections.statusCollection')">
      <dl class="detail-grid">
        <div
          v-for="item in statusItems"
          :key="item.label"
          class="detail-field"
        >
          <dt>{{ item.label }}</dt>
          <dd>{{ item.value }}</dd>
        </div>
      </dl>
    </SectionBlock>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from "vue-i18n";
import AgentCodePreview from "@/modules/agent/components/AgentCodePreview.vue";
import type { AgentDetailTextItem } from "@/modules/agent/lib/agent-detail-view";
import SectionBlock from "@/shared/ui/page/SectionBlock.vue";

defineProps<{
  connectionItems: AgentDetailTextItem[];
  authItems: AgentDetailTextItem[];
  statusItems: AgentDetailTextItem[];
  customRequestBodyJson: string;
}>();

const { t } = useI18n();
</script>

<style scoped lang="scss">
.agent-connection-panel {
  display: contents;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.35rem 1.15rem;
}

.detail-field {
  min-width: 0;
  padding: 0.72rem 0;
  border-top: 1px solid var(--color-border-soft);
  transition:
    border-color var(--duration-fast) var(--ease-standard),
    background var(--duration-fast) var(--ease-standard);
}

.detail-field:hover {
  border-color: var(--color-border-strong);
  background: linear-gradient(90deg, rgba(99, 102, 241, 0.06), transparent 72%);
}

.detail-grid .detail-field:nth-child(-n + 2) {
  border-top-color: transparent;
}

.detail-field dt {
  color: var(--color-text-subtle);
  font-size: 0.86rem;
}

.detail-field dd {
  margin: 0.32rem 0 0;
  color: var(--color-text-dark);
  font-weight: 700;
  overflow-wrap: anywhere;
  line-height: 1.55;
}

@media (max-width: 700px) {
  .detail-grid {
    grid-template-columns: 1fr;
  }

  .detail-grid .detail-field:nth-child(-n + 2) {
    border-top-color: var(--color-border-soft);
  }

  .detail-grid .detail-field:first-child {
    border-top-color: transparent;
  }
}
</style>
